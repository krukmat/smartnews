import os
from functools import wraps
from contextlib import contextmanager, nested

from fabric.api import (
    cd, run as _run, task, env, hide, sudo as _sudo
)
from fabric.colors import red, green, blue, yellow
from fabric.context_managers import prefix
from fabric.operations import require as require_env, open_shell
from fabric.contrib.files import exists
import fabtools

__author__ = 'matiasleandrokruk'

LOG_PATH = '/var/log/supervisor/%s.log'

################
# Config setup #
################


env.project_name = 'smartnews'

# env.user = env.project_name
env.password = 'qwerty123'
env.db_user = env.project_name
env.db_name = env.project_name
env.db_password = env.project_name
env.db_host = '127.0.0.1'
env.db_test_name = env.db_name + '_test'

env.debian_packages = "debian_packages.txt"
env.cassandra_packages = "debian_cassandra.txt"

env.git_url = 'ssh://krukmat@github.com/krukmat/smartnews'

env.python = 'python'
env.virtualenv_path = os.path.join('venv')
env.nodeenv_path = os.path.join('~', 'nenv')
env.project_path = os.path.join('/home/vagrant', env.project_name)
env.project_wsgi = '.'.join(['django_app', 'django_app'])

env.django_static_url = '/static/'
env.django_static_root = os.path.join(env.project_path, 'static/')
env.cdn_static_root = os.path.join(env.project_path, 'dummy/cdn/')
env.user_site_static_root = os.path.join(env.project_path, 'dummy/usersite/')

env.uwsgi_socket_dir = '/tmp/'
env.uwsgi_socket = os.path.join(env.uwsgi_socket_dir, 'uwsgi.sock')
env.uwsgi_socket_web = os.path.join(env.uwsgi_socket_dir, 'web.sock')


env.django_static_url = '/static/'
env.django_static_root = os.path.join(env.project_path, 'static/')
env.cdn_static_root = os.path.join(env.project_path, 'dummy/cdn/')
env.user_site_static_root = os.path.join(env.project_path, 'dummy/usersite/')


env.config_file = '__init__.py'
env.local_config_file = 'local.py'

env.frontend_ip = '0.0.0.0'

env.ruby_version = '2.0.0'


def environment(func):
    @wraps(func)
    def update_env(*args, **kawrgs):
        env['is_%s' % func.__name__] = True
        return func(*args, **kawrgs)
    return update_env

@task
@environment
def production():
    """[ENV]"""
    env.hosts = ['0.0.0.0']
    env.django_settings = 'webserver.settings.prod'


@task
def configure_supervisor():
    """Configure supervisor processes"""

    SUPERVISOR_TASKS = dict(
        django={},
        scrapers={}
    )

    require_env('project_path', 'virtualenv_path', 'frontend_ip',
                'django_settings', 'project_user')

    SUPERVISOR_TASKS['django']['command'] = (
        '/home/vagrant/smartnews/venv/bin/uwsgi --module %s.wsgi --socket %s --chmod-socket=666'
        % (env.project_wsgi, env.uwsgi_socket))

    SUPERVISOR_TASKS['django']['directory'] = env.project_path

    SUPERVISOR_TASKS['scrapers']['command'] = (
        '%s/bin/run_celery' % env.project_path
    )
    SUPERVISOR_TASKS['scrapers']['directory'] = env.project_path

    for process_name, options in SUPERVISOR_TASKS.iteritems():

        kwargs = dict(
            directory=options['directory'],
            environment='PYTHONPATH="%s"' % os.path.join(env.project_path, 'django_app'),
            autostart='true',
            autorestart='false',
            master='true',
            startsecs=3,
            user=env.supervisor_user,
            loglevel='debug',
            virtualenv='/home/vagrant/smartnews/venv/',
        )

        options['command'] = options['command'].format(env.virtualenv_path)

        process_kwargs = kwargs.copy()

        process_kwargs.update(
            stdout_logfile=LOG_PATH % process_name,
            **options
        )
        sudo('touch /var/log/%s.log' % (process_name))
        fabtools.require.file('/var/log/%s.log' % (process_name))
        sudo('chown %s:%s /var/log/%s.log' % (env.supervisor_user,
                                              env.supervisor_user,
                                              process_name))

        for key in process_kwargs:
            if callable(process_kwargs[key]):
                process_kwargs[key] = process_kwargs[key]()

        fabtools.require.supervisor.process(process_name, **process_kwargs)

    # autostart: attached supervisord for /etc/init.d/ if needed
    if not exists('/etc/init.d/supervisor', use_sudo=True):
        sudo('update-rc.d supervisor defaults')

@task
def restart_supervisor():
    sudo('service supervisor restart')


@task
def supervisor(command, *processes):
    """Usage: `fab <env> supervisor:"<command>,<process1>,<process2>,..."`"""
    if command in ('start', 'stop', 'restart', 'status'):
        if processes:
            processes = set(processes).intersection(env.supervisor_apps)
        else:
            processes = env.supervisor_apps

        if processes:
                for process_name in processes:
                    run('sudo supervisorctl %s %s:' % (command, process_name))

        else:
            _print(red('No valid processes specified, aborting.', bold=True))

    else:
        _print(red('Unknown supervisor command: %s, aborting.' % command,
                   bold=True))

@task
def configure_nginx():
    """Configure nginx"""
    require_env('django_static_url', 'django_static_root', 'cdn_static_root',
                'user_site_static_root', 'uwsgi_socket',
                'uwsgi_socket_web')

    django_config = """
            upstream django {
                server unix://%(uwsgi_socket)s;
            }

            upstream web {
                server unix://%(uwsgi_socket_web)s;
            }

            server {
                listen %(port)s;
                server_name %(server_name)s;

                client_max_body_size 50M;

                access_log /var/log/nginx/%(server_name)s.log;
                error_log /var/log/nginx/%(server_name)s_error.log;

                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header Host $http_host;

                location /static/ {
                    alias %(django_static_root)s;
                    sendfile off;
                }


                location / {
                    uwsgi_pass  django;
                    include     uwsgi_params;
                }

                location /web/ {
                    rewrite /web/(.+) /$1 break;
                    uwsgi_pass web;
                    include    uwsgi_params;
                }

            }
        """

    static_config = """
            server {
                listen %(port)s;
                server_name %(server_name)s;

                access_log /var/log/nginx/%(server_name)s.log;
                error_log /var/log/nginx/%(server_name)s_error.log;

                location / {
                    alias %(static_root)s;
                    sendfile off;
                }
            }
        """

    live_config = """
            server {
                listen %(port)s;
                server_name %(server_name)s;

                access_log /var/log/nginx/%(server_name)s.log;
                error_log /var/log/nginx/%(server_name)s_error.log;

                location %(location)s {
                    proxy_pass http://127.0.0.1:9000/;
                }
            }
        """

    django_kwargs = dict(
        port=80,
        django_static_url=env.django_static_url,
        django_static_root=env.django_static_root,
        uwsgi_socket=env.uwsgi_socket,
        uwsgi_socket_web=env.uwsgi_socket_web,
        )

    cdn_kwargs = dict(
        port=80,
        static_root=env.cdn_static_root
    )

    user_site_kwargs = dict(
        port=80,
        static_root=env.user_site_static_root,
        )


    user_site_live_kwargs = dict(
        port=80,
        location='/',
        )

    fabtools.require.nginx.server()
    fabtools.require.nginx.disable('default')

    fabtools.require.nginx.site('smartnews.dev', django_config, **django_kwargs)
    fabtools.require.nginx.site('cdn.smartnews.dev', static_config, **cdn_kwargs)
    fabtools.require.nginx.site('smartnews.usersite.dev', static_config,
                                **user_site_kwargs)
    fabtools.require.nginx.site('smartnews.usersite.live', live_config,
                                **user_site_live_kwargs)

@task
@environment
def vagrant(name=''):
    """[ENV]"""
    from fabtools.vagrant import vagrant as _vagrant
    _vagrant(name)
    env.project_user = 'vagrant'
    env.supervisor_user = 'vagrant'
    env.supervisor_apps = ['django', 'scrapers']
    env.django_settings = 'django_app.django_app.settings'
    env.django_path = '/home/vagrant/smartnews/django_app'


def _print(output):
    print os.linesep, output, os.linesep


def print_command(command):
    _print(blue("$ ", bold=True) +
           yellow(command, bold=True) +
           red(" ->", bold=True))

@task
def run(command, show=True, args=("running",), quiet=False, shell=True):
    """Runs a shell comand on the remote server."""

    if show:
        print_command(command)
    else:
        args += ('stdout',)

    with hide(*args):
        return _run(command, quiet=quiet, shell=True)

@task
def sudo(command, show=True, shell_escape=None, shell=True):
    """Runs a command as sudo on the remote server."""
    if show:
        print_command(command)
    with hide("running"):
        return _sudo(command, shell_escape=shell_escape, shell=shell)

@task
def install_virtualenv():
    """
    Create a new virtual environment for a project.
    """

    require_env('virtualenv_path', 'project_path')

    # Replaces fabtools version since ther is some bug with pip install script
    # looks like curl fails on redirect.
    fabtools.deb.install('python-pip')
#     fabtools.python.install_pip()

    fabtools.python.install('virtualenv', use_sudo=True)

    if exists(env.virtualenv_path):
        run('rm -r %s' % env.virtualenv_path)

    # Create virtualenv
    run('virtualenv --no-site-packages -p %s --distribute %s' %
        (env.python, env.virtualenv_path))

    if not exists('~/activate'):
        run('ln -s %s/bin/activate ~/activate' % env.virtualenv_path)

        with cd(env.virtualenv_path):
            append_extract = 'export PYTHONPATH=%s' % env.project_path
            sudo('echo "%s" >> bin/activate' % append_extract)

    # Make shortcut
    sudo('ln -sf %s %s' % (env.virtualenv_path, os.path.join(env.project_path, 'venv')))

    _print(green('virtualenv installed'))

    # Make shortcut
    sudo('ln -sf %s %s' % (env.virtualenv_path, os.path.join(env.project_path, 'venv')))

@task
def install_git_repository(branch=None):
    require_env('project_path', 'git_url')

    if not exists(env.project_path):
        if env.get('is_vagrant') and exists('/vagrant'):
            run('ln -s /vagrant %s' % env.project_path)
        else:
            # not tested on testing/staging
            fabtools.require.directory(env.project_path)
            fabtools.git.clone(env.git_url, path=env.project_path)

    if branch:
        fabtools.git.checkout(env.project_path, branch=branch)

@contextmanager
def project():
    """Runs commands within the project's directory."""
    require_env('project_path', 'virtualenv_path')

    with fabtools.python.virtualenv(env.virtualenv_path):
        with cd(env.project_path):
            yield


@contextmanager
def root_path():
    with fabtools.python.virtualenv(env.virtualenv_path):
        with cd('~'):
            yield

@task
def install_python_modules():
    with project():
        fabtools.python.install_requirements('requirements.txt')
    with root_path():
        run(""" python -m nltk.downloader all""")

@task
def install_wikicorpus_es():
    run('curl http://www.cs.upc.edu/~nlp/wikicorpus/tagged.es.tgz | tar xvz')


def cassandra_sources():
    run('curl -L http://debian.datastax.com/debian/repo_key | sudo apt-key add -')
    # Cassandra and DevOp Center source
    fabtools.require.deb.source('cassandra',
                                'http://debian.datastax.com/community',
                                '',
                                'stable main')
    # Oracle Java 7 install source. It's needed for Cassandra.
    fabtools.require.deb.ppa('ppa:webupd8team/java')
    run('apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys EEA14886')
    run('echo oracle-java7-installer shared/accepted-oracle-license-v1-1 '
        'select true | sudo /usr/bin/debconf-set-selections')  #

@task
def install_debian_packages():

    require_env('debian_packages')
    fabtools.deb.update_index()

    filename = os.path.join(os.path.dirname(__file__),
                            env.debian_packages)

    with open(filename, 'r') as file_:
        packages = [line.strip() for line in file_]

    fabtools.deb.install(packages)
    fabtools.deb.upgrade()


@task
def install_debian_cassandra():
    # debian_cassandra has all the requirements to install cassandra
    require_env('cassandra_packages')
    cassandra_requirements = os.path.join(os.path.dirname(__file__),
                                          env.cassandra_packages)
    with open(cassandra_requirements, 'r') as file_:
        packages = [line.strip() for line in file_]
    cassandra_sources()
    fabtools.deb.install(packages)
    fabtools.deb.upgrade()


@task
def configure_redis():
    """Configure redis via supervisor"""

    kwargs = dict(
        command='redis-server',
        stdout_logfile='/var/log/supervisor/redis.log',
        user='root',
        exitcodes='0',
        startsecs=1,
        autorestart='unexpected',
        startretries=1,
        priority=1
    )
    fabtools.require.supervisor.process('redis', **kwargs)

@task
def update_repos():
    run('sudo add-apt-repository ppa:mc3man/trusty-media')
    run('sudo add-apt-repository ppa:chris-lea/redis-server')
    run('sudo apt-get update')

@task
def install():
    update_repos()
    install_git_repository()
    install_virtualenv()
    install_debian_packages()
    install_debian_cassandra()
    install_python_modules()
    # install_wikicorpus_es()
    install_stop_words()
    configure_nginx()
    configure_redis()
    configure_cassandra()
    configure_supervisor()

@task
def django_manage(command, *args, **kwargs):
    with root_path():
        str_args = ' '.join(args)
        str_kwargs = ' '.join(['%s=%s' % (k, v) for k, v in kwargs.items()])
        run('DJANGO_SETTINGS_MODULE="%s" python smartnews/django_app/manage.py %s %s %s' %
                ("django_app.settings", command, str_args, str_kwargs))

@task
def test(*args, **kwargs):
    with root_path():
        str_args = ' '.join(args)
        str_kwargs = ' '.join(['%s=%s' % (k, v) for k, v in kwargs.items()])
        run('DJANGO_SETTINGS_MODULE="%s" python smartnews/django_app/manage.py test %s %s' %
                ("django_app.settings", str_args, str_kwargs))

@task
def configure_cassandra():
    """Configure cassandra: move to supervisor"""
    run('sudo mkdir -p /var/lib/cassandra/data')  # It doesn't create it by default
    run('sudo chown cassandra:cassandra /var/lib/cassandra/data')  # Change ownership to cassandra user
    kwargs = dict(
        command='service cassandra start',
        stdout_logfile='/var/log/supervisor/cassandra.log',
        user='root',
        exitcodes='0',
        startsecs=0,
        autorestart='unexpected',
        startretries=1,
        priority=1
    )
    fabtools.require.supervisor.process('cassandra', **kwargs)

@task
def install_stop_words():
    #TODO: Should be in another place...
    with cd('/home/vagrant/venv/lib/python2.7/site-packages/stop_words/'):
        run("git clone https://github.com/Alir3z4/stop-words.git", quiet=True)


@task
def install_rvm():
    """
    Install rvm
    """
    require_env('ruby_version')
    run('gpg --keyserver hkp://keys.gnupg.net --recv-keys D39DC0E3')
    run('curl -L https://get.rvm.io | bash -s stable')

    if not exists('~/.rvm/'):
        run('ln -sd /usr/local/rvm ~/.rvm')

    run('source ~/.rvm/scripts/rvm')
    run('rvm install %s' % env.ruby_version)

@task
def install_nodeenv():
    """
    Install nodeenv
    """
    require_env('nodeenv_path')

    nodejs_path = '/usr/bin/nodejs'
    node_path = '/usr/bin/node'
    # if not exists(node_path):
    #    sudo('ln -s %s %s' % (nodejs_path, node_path))

    if exists(env.nodeenv_path):
        run('rm -r %s' % env.nodeenv_path)

    with project():
        run('nodeenv --node=system %s' % env.nodeenv_path)

@contextmanager
def rvm():
    """Runs commands within rvm."""
    require_env('ruby_version')
    with nested(prefix("source ~/.rvm/scripts/rvm"),
                prefix('rvm %s' % env.ruby_version)):
        yield

@contextmanager
def nodeenv():
    """Runs commands within nodeenv."""
    require_env('nodeenv_path')

    with nested(prefix("source %s/bin/activate" % env.nodeenv_path)):
        yield

@task
def install_app_requirements():
    with nodeenv():
        run('npm install -g gulp bower')

@task
def install_compass():
    """
    Install compass
    """
    with rvm():
        run('gem update --system')
        run('gem install compass')

@task
def install_frontend():
    install_rvm()
    install_nodeenv()
    install_compass()
    install_app_requirements()

@task
def sync():
    django_manage('sync_cassandra')

@task
def update():
    install_debian_packages()
    install_debian_cassandra()
    install_virtualenv()
    install_python_modules()
    restart_supervisor()