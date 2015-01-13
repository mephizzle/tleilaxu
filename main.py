from os import makedirs, path, unlink
import tarfile

from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.properties import (
    ObjectProperty,
    StringProperty
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.storage.jsonstore import JsonStore


class Storage(JsonStore):
    def get(self, name, default):
        try:
            return super(Storage, self).get(name)
        except KeyError:
            return default
storage = Storage('tleilax.json')


KIVY_ROOT_DIR = '/sdcard/kivy/'


class TleilaxScreen(Screen):
    def __init__(self, *args, **kwargs):
        super(TleilaxScreen, self).__init__(*args, **kwargs)
        self.app = App.get_running_app()


class OutputScreen(TleilaxScreen):
    host = StringProperty()

    def on_enter(self):
        self.clear_widgets()
        self.box = BoxLayout(orientation='vertical')
        self.add_widget(self.box)
        self.message('running deployment...')

        def tar_callback(req, response):
            self.message('code received, deploying')
            self.projectfolder = path.join(KIVY_ROOT_DIR, self.name)
            try:
                self.message('making folder {0}...'.format(self.projectfolder))
                makedirs(self.projectfolder)
            except OSError:
                self.message('folder exists, skipping')
            with open(
                    path.join(self.projectfolder, 'tl_package.tar'),
                    'w'
            ) as outf:
                outf.write(response)
            self.finish()

        def name_callback(req, response):
            self.name = response.strip()
            self.message('name found ({0})'.format(self.name))
            self.message('getting code...')
            UrlRequest(
                '/'.join([self.host, '.tl_build/tl_package.tar']),
                tar_callback
            )

        self.message('retrieving project name (folder)...')
        UrlRequest(
            '/'.join([self.host, '.tl_build/name.conf']),
            name_callback
        )

    def message(self, msg):
        self.box.add_widget(
            Label(
                text=msg,
                size_hint_y=None,
                height='30sp'
            )
        )

    def finish(self):
        self.message('unpacking code...')
        tfn = path.join(self.projectfolder, 'tl_package.tar')

        with tarfile.TarFile(tfn) as f:
            f.extractall(self.projectfolder)
        self.message('cleaning up...')
        unlink(tfn)
        self.message('done')


class MainScreen(TleilaxScreen):
    ip = ObjectProperty()
    port = ObjectProperty()

    def do_deploy(self):
        self.app.ip = self.ip.text
        self.app.port = self.port.text

        output = OutputScreen()

        output.host = 'http://{0}:{1}'.format(
            self.ip.text,
            self.port.text
        )

        self.manager.add_widget(output)
        self.manager.current = output.name


class TleilaxApp(App):
    def __init__(self, *args, **kwargs):
        super(TleilaxApp, self).__init__(*args, **kwargs)
        self.load()

    def load(self):
        host = storage.get('host', {})
        self.ip = host.get('ip', '192.168.1.1')
        self.port = host.get('port', '8080')

    def save(self):
        host = {
            'ip': self.ip,
            'port': self.port
        }
        storage.put('host', **host)

    def on_stop(self):
        self.save()


TleilaxApp().run()
