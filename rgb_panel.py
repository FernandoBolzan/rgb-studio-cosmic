#!/usr/bin/python3
"""RGB Studio: desktop lighting controls for COSMIC, powered by OpenRGB."""
import concurrent.futures
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
from colorsys import hsv_to_rgb, rgb_to_hsv
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, Gdk, GLib, AyatanaAppIndicator3 as Indicator

BASE = Path.home() / '.local/share/rgb-panel'
BUNDLED_OPENRGB = BASE / 'openrgb/AppRun'
OPENRGB = (os.environ.get('RGB_PANEL_OPENRGB') or
           (str(BUNDLED_OPENRGB) if BUNDLED_OPENRGB.exists() else
            shutil.which('openrgb') or str(BUNDLED_OPENRGB)))
CONFIG = Path.home() / '.config/rgb-panel/settings.json'
PRESETS = Path.home() / '.config/rgb-panel/presets'
DEFAULT_ZONE_LEDS = 500
QUICK = [
    ('Verde vivo', '#39D353'), ('Esmeralda', '#00A86B'),
    ('Menta', '#75F0C0'), ('Azul gelo', '#79D8FF'),
    ('Azul noite', '#4267E8'), ('Roxo', '#A879FF'),
    ('Rosa', '#FF70A6'), ('Âmbar', '#FFB547'),
]
SPECTRUM_SWATCHES = [
    ('Vermelho', '#F04452'), ('Coral', '#FF654A'), ('Laranja', '#FF8B32'),
    ('Âmbar', '#FFB547'), ('Amarelo', '#F2D84B'), ('Lima', '#B8E34B'),
    ('Verde', '#39D353'), ('Esmeralda', '#00A86B'), ('Turquesa', '#2CCBA5'),
    ('Ciano', '#38C7E9'), ('Azul céu', '#458DE0'), ('Azul', '#4267E8'),
    ('Índigo', '#5748C4'), ('Violeta', '#9861E8'), ('Roxo', '#A879FF'),
    ('Magenta', '#D45ACD'), ('Rosa', '#F36184'), ('Rosa claro', '#FF80A5'),
]
MODE_LABELS = {
    'direct': 'Cor fixa', 'static': 'Cor fixa', 'off': 'Desligado',
    'breathing': 'Respirar', 'flashing': 'Piscar',
    'spectrum cycle': 'Ciclo de cores', 'rainbow': 'Arco-íris',
    'chase fade': 'Rastro suave', 'chase': 'Rastro',
    'color shift': 'Alternar cores', 'color pulse': 'Pulso de cor',
    'rainbow wave': 'Onda arco-íris', 'color wave': 'Onda colorida',
    'visor': 'Varredura', 'rain': 'Chuva', 'marquee': 'Letreiro',
    'sequential': 'Sequencial', 'spectrum cycle breathing': 'Respiração colorida',
    'spectrum cycle chase fade': 'Rastro colorido suave',
    'spectrum cycle chase': 'Rastro colorido',
    'spectrum cycle wave': 'Onda colorida',
    'chase rainbow pulse': 'Pulso arco-íris', 'random flicker': 'Brilho aleatório',
    'gentle transition': 'Transição suave', 'wave propagation': 'Onda expansiva',
    'wave propagation pause': 'Onda expansiva com pausa', 'red pulse': 'Pulso vermelho',
}
CSS = b'''
window.rgb-window { background-color: #111613; color: #EEF4EF; font-family: "Noto Sans", sans-serif; }
.rgb-header { background-color: #151C18; border-bottom: 1px solid #2B3730; padding: 11px 18px; }
.rgb-wordmark { color: #F0F6F1; font-size: 18px; font-weight: 800; letter-spacing: .08em; }
.rgb-kicker { color: #A6B4A9; font-size: 11px; font-weight: 700; letter-spacing: .13em; }
.rgb-title { color: #F1F6F2; font-size: 23px; font-weight: 700; }
.rgb-subtitle, .rgb-muted { color: #A5B2A8; font-size: 12px; }
.rgb-sidebar { background-color: #151C18; border-right: 1px solid #2B3730; padding: 18px 12px; }
button.device-row { background: transparent; border: 1px solid transparent; border-radius: 8px; color: #DDE6DF; padding: 10px 9px; }
button.device-row:hover { background-color: #202923; }
button.device-row.selected { background-color: #26352A; border-color: #55734E; }
.device-name { color: #EFF5F0; font-size: 12px; font-weight: 700; }
.device-meta { color: #9DACA1; font-size: 10px; }
.device-dot { color: #B9F27B; font-size: 15px; }
.rgb-content { padding: 14px 18px; }
.rgb-workspace { padding: 0; }
.rgb-panel { background-color: #171E1A; border: 1px solid #2B3830; border-radius: 10px; padding: 13px; }
.rgb-color-panel { padding-top: 10px; padding-bottom: 10px; }
.rgb-zone { background-color: #1A211C; border: 1px solid #354236; border-radius: 9px; padding: 15px; }
.rgb-heading { color: #EEF4EF; font-size: 15px; font-weight: 700; }
.rgb-number { color: #F5F8F5; font-family: monospace; font-size: 14px; font-weight: 700; }
.rgb-status { background-color: #202923; border: 1px solid #344239; border-radius: 15px; color: #C4D0C6; padding: 5px 10px; font-size: 11px; }
.rgb-status.good { background-color: #1B3020; border-color: #3C6842; color: #C9F2BB; }
.rgb-status.error { background-color: #382220; border-color: #78463D; color: #FFD0C8; }
button.rgb-primary { background-image: none; background-color: #B9F27B; border: 1px solid #B9F27B; border-radius: 7px; color: #182312; padding: 9px 15px; font-weight: 800; }
button.rgb-primary:hover { background-image: none; background-color: #CDF99B; }
button.rgb-primary:disabled { background-color: #53614A; color: #C0C8BA; }
button.rgb-secondary { background-image: none; background-color: #252E28; border: 1px solid #3A473E; border-radius: 7px; color: #E3EBE5; padding: 8px 12px; }
button.rgb-secondary:hover { background-image: none; background-color: #303C33; }
button.rgb-swatch { background-image: none; border: 1px solid rgba(255,255,255,.38); border-radius: 7px; min-width: 28px; min-height: 28px; padding: 0; }
entry { background-color: #121814; border: 1px solid #3B4940; border-radius: 6px; color: #EDF4EE; padding: 7px 9px; }
entry:focus { border-color: #B9F27B; }
entry.invalid { border-color: #E77A6B; }
combobox, combobox cellview, combobox button, button.combo, spinbutton, spinbutton entry, spinbutton button { background-image: none; background-color: #202923; border-color: #3B4940; color: #EFF4F0; }
combobox arrow { color: #DDE8DF; }
.rgb-footer { background-color: #151C18; border-top: 1px solid #2B3730; padding: 8px 18px; }
scale trough { background-color: #303B33; min-height: 4px; }
scale highlight { background-color: #B9F27B; }
scale slider { background-color: #E8F1E8; border: 1px solid #7C907B; min-width: 14px; min-height: 14px; }
flowbox, flowboxchild { background-color: transparent; }
separator { background-color: #303B34; }
button:focus, entry:focus, scale:focus, combobox:focus { outline-color: #B9F27B; }
'''

def parse_devices(output):
    devices = []
    for line in output.splitlines():
        match = re.match(r'^(\d+): (.+)$', line)
        if match:
            devices.append({'id': match[1], 'name': match[2], 'modes': [], 'zones': []})
        elif devices and line.strip().startswith('Modes:'):
            devices[-1]['modes'] = [m.strip('[]') for m in shlex.split(line.split(':', 1)[1].strip())]
        elif devices and line.strip().startswith('Zones:'):
            devices[-1]['zones'] = shlex.split(line.split(':', 1)[1].strip())
    return devices


class ColorCanvas:
    """Full-spectrum HSV field with one direct pointer target."""
    def __init__(self, changed):
        self.changed = changed
        self.hue, self.saturation, self.value = 0.34, 0.82, 0.88
        self.dragging = False
        self.base = Gtk.EventBox()
        self.widget = self.base
        self.base.set_name('rgb-color-base')
        self.base.set_size_request(370, 100)
        self.base.set_can_focus(True)
        self.base.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.BUTTON1_MOTION_MASK)
        self.base.set_tooltip_text(
            'Arraste horizontalmente para mudar de matiz e verticalmente para mudar o brilho')
        self.base.get_accessible().set_name(
            'Espectro de cores: arraste na horizontal para escolher o matiz e na vertical para escolher o brilho')
        self.base_provider = Gtk.CssProvider()
        self.base.get_style_context().add_provider(
            self.base_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.base.connect('button-press-event', self.pointer_press)
        self.base.connect('motion-notify-event', self.pointer_motion)
        self.base.connect('button-release-event', self.pointer_release)
        self.base.connect('key-press-event', self.key_press)
        self.base.connect('size-allocate', self.position_marker)
        self.update_spectrum()

    def update_spectrum(self):
        stops = []
        for index in range(13):
            hue = index / 12
            rgb = tuple(round(value * 255) for value in hsv_to_rgb(
                hue, self.saturation, 1))
            stops.append('#%02X%02X%02X %.3f%%' % (*rgb, hue * 100))
        gradient = ', '.join(stops)
        width = self.base.get_allocated_width()
        height = self.base.get_allocated_height()
        if width < 18:
            width = 370
        if height < 18:
            height = 100
        x = round(9 + self.hue * (width - 18))
        y = round(9 + (1 - self.value) * (height - 18))
        marker = (
            'radial-gradient(circle 9px at %dpx %dpx, '
            'rgba(17,22,19,.55) 0%%, rgba(17,22,19,.55) 60%%, '
            '#FFFFFF 72%%, #FFFFFF 86%%, rgba(0,0,0,0) 100%%)' % (x, y))
        css = (
            f'#rgb-color-base {{ background-image: {marker}, '
            f'linear-gradient(to bottom, rgba(0,0,0,0), rgba(0,0,0,1)), '
            f'linear-gradient(to right, {gradient}); border-radius: 8px; }}')
        self.base_provider.load_from_data(css.encode())

    def set_color(self, color):
        rgb = tuple(int(color[i:i+2], 16) / 255 for i in (1, 3, 5))
        self.hue, self.saturation, self.value = rgb_to_hsv(*rgb)
        self.update_spectrum()

    def set_saturation(self, saturation):
        self.saturation = max(0.0, min(1.0, saturation))
        self.update_spectrum()

    def emit_color(self):
        rgb = tuple(round(value * 255) for value in hsv_to_rgb(
            self.hue, self.saturation, self.value))
        self.changed('#%02X%02X%02X' % rgb)
        self.update_spectrum()

    def choose(self, x, y):
        width = max(1, self.base.get_allocated_width())
        height = max(1, self.base.get_allocated_height())
        self.hue = max(0.0, min(1.0, x / max(1, width - 1)))
        self.value = 1 - max(0.0, min(1.0, y / max(1, height - 1)))
        self.emit_color()

    def pointer_press(self, _widget, event):
        if event.button != 1:
            return False
        self.dragging = True
        self.base.grab_focus()
        self.choose(event.x, event.y)
        return True

    def pointer_motion(self, _widget, event):
        if self.dragging and event.state & Gdk.ModifierType.BUTTON1_MASK:
            self.choose(event.x, event.y)
            return True
        return False

    def pointer_release(self, _widget, event):
        if self.dragging and event.button == 1:
            self.choose(event.x, event.y)
            self.dragging = False
            return True
        return False

    def key_press(self, _widget, event):
        if event.keyval == Gdk.KEY_Left:
            self.hue = max(0.0, self.hue - 1 / 360)
        elif event.keyval == Gdk.KEY_Right:
            self.hue = min(1.0, self.hue + 1 / 360)
        elif event.keyval == Gdk.KEY_Up:
            self.value = min(1.0, self.value + 0.02)
        elif event.keyval == Gdk.KEY_Down:
            self.value = max(0.0, self.value - 0.02)
        else:
            return False
        self.emit_color()
        return True

    def position_marker(self, *_):
        self.update_spectrum()

class Panel:
    def __init__(self):
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.devices = []
        self.target_specs = {}
        self.selected_target = 'all'
        self.busy = False
        self.startup_restore_started = False
        self.startup_restore_attempts = 0
        self.window = None
        self.settings = self.load_settings()
        self.selected_target = self.settings.get('target') or 'all'
        self.selected_color = self.settings.get('color', '#39D353')
        self._syncing_color = False
        self._laying_out = None
        self.detected = False
        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), self.provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.indicator = Indicator.Indicator.new(
            'rgb-panel', str(BASE / 'rgb-panel.svg'), Indicator.IndicatorCategory.HARDWARE)
        self.indicator.set_status(Indicator.IndicatorStatus.ACTIVE)
        self.indicator.set_title('RGB Studio')
        self.build_menu('Procurando dispositivos…')
        self.refresh()

    def load_settings(self):
        defaults = {
            'zone_led_count': DEFAULT_ZONE_LEDS,
            'color': '#39D353',
            'target': None,
            'target_label': None,
            'target_kind': None,
            'mode': None,
            'brightness': 100,
            'speed': 50,
            'restore_on_startup': False,
        }
        try:
            data = json.loads(CONFIG.read_text(encoding='utf-8'))
            count = int(data.get('zone_led_count', DEFAULT_ZONE_LEDS))
            color = str(data.get('color', '#39D353')).upper()
            if not re.fullmatch(r'#[0-9A-F]{6}', color):
                color = '#39D353'
            target = data.get('target')
            target_label = data.get('target_label')
            target_kind = data.get('target_kind')
            mode = data.get('mode')
            restore_on_startup = data.get('restore_on_startup', 'color' in data)
            if not isinstance(restore_on_startup, bool):
                restore_on_startup = 'color' in data
            return {
                'zone_led_count': max(1, min(500, count)),
                'color': color,
                'target': target if isinstance(target, str) else None,
                'target_label': target_label if isinstance(target_label, str) else None,
                'target_kind': target_kind if isinstance(target_kind, str) else None,
                'mode': mode if isinstance(mode, str) else None,
                'brightness': max(0, min(100, int(data.get('brightness', 100)))),
                'speed': max(0, min(100, int(data.get('speed', 50)))),
                # Old settings files contain a color written only after applying it.
                'restore_on_startup': restore_on_startup,
            }
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return defaults

    def save_settings(self):
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(json.dumps(self.settings, indent=2), encoding='utf-8')

    def command(self, args):
        result = subprocess.run(
            [OPENRGB, '--noautoconnect', *args],
            capture_output=True, text=True, timeout=45)
        combined = result.stdout + result.stderr
        if result.returncode or 'Connection attempt failed' in combined:
            raise RuntimeError((result.stderr or result.stdout or
                                'O OpenRGB não conseguiu aplicar o ajuste')[-1800:])
        return result.stdout

    def submit(self, job, done, quiet=False):
        if self.busy:
            return
        self.busy = True
        self.set_status('Aplicando…', 'pending')
        self.set_busy_controls(True)
        future = self.pool.submit(job)
        future.add_done_callback(
            lambda result: GLib.idle_add(self.finish, result, done, quiet))

    def finish(self, future, done, quiet=False):
        self.busy = False
        self.set_busy_controls(False)
        menu_status = 'Pronto'
        try:
            done(future.result())
            if quiet:
                menu_status = 'Configuração reaplicada'
        except Exception as error:
            logging.exception('RGB action failed')
            self.set_status('Falha ao aplicar', 'error')
            if quiet:
                if self.startup_restore_attempts < 3:
                    GLib.timeout_add_seconds(5, self.retry_startup_restore)
                    menu_status = 'Tentando restaurar…'
                else:
                    logging.error('Could not restore saved RGB settings after three attempts')
                    menu_status = 'Falha ao restaurar'
            else:
                dialog = Gtk.MessageDialog(
                    transient_for=self.window, modal=True, message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.CLOSE, text='Não consegui aplicar esse ajuste')
                dialog.format_secondary_text(str(error))
                dialog.connect('response', lambda box, _response: box.destroy())
                dialog.show_all()
        self.build_menu(menu_status if not self.busy else 'Aplicando…')
        return False

    def retry_startup_restore(self):
        self.restore_saved_configuration()
        return False

    def refresh(self, *_):
        self.submit(
            lambda: parse_devices(self.command(['--list-detailed'])),
            self.loaded)

    def loaded(self, devices):
        self.devices = devices
        self.detected = True
        self.rebuild_targets()
        self.build_menu(f'{len(devices)} dispositivos')
        self.set_status(
            f'{len(devices)} dispositivos encontrados' if devices else 'Nenhum dispositivo RGB detectado',
            'good' if devices else 'error')
        if (devices and self.settings.get('restore_on_startup') and
                not self.startup_restore_started):
            self.startup_restore_started = True
            self.restore_saved_configuration()

    def preferred_mode(self, devices, requested=None):
        if not devices:
            return None
        common_modes = set(devices[0]['modes'])
        for device in devices[1:]:
            common_modes &= set(device['modes'])
        if requested in common_modes:
            return requested
        return next((mode for mode in ('Direct', 'Static') if mode in common_modes),
                    next(iter(sorted(common_modes)), None))

    def target_for_devices(self, devices, preferred=None):
        device_ids = {device['id'] for device in devices}
        if preferred in self.target_specs:
            preferred_ids = {
                device['id'] for device in self.target_specs[preferred]['devices']
            }
            if preferred_ids == device_ids:
                return preferred
        for key, spec in self.target_specs.items():
            if spec['kind'] == 'zone':
                continue
            if {device['id'] for device in spec['devices']} == device_ids:
                return key
        if len(device_ids) == 1:
            key = f'device:{next(iter(device_ids))}'
            if key in self.target_specs:
                return key
        return None

    def restore_saved_configuration(self):
        if not self.devices or self.startup_restore_attempts >= 3:
            return
        self.startup_restore_attempts += 1

        target_key = self.settings.get('target') or 'all'
        spec = self.target_specs.get(target_key)
        if not spec and self.settings.get('target_label'):
            matches = [candidate for candidate in self.target_specs.values()
                       if candidate['label'] == self.settings['target_label'] and
                       candidate['kind'] == self.settings.get('target_kind')]
            if len(matches) == 1:
                spec = matches[0]
                target_key = spec['key']
        if not spec:
            logging.warning('Saved RGB target %r is unavailable; skipping startup restore',
                            target_key)
            self.set_status('O componente salvo não foi encontrado', 'error')
            return

        devices = spec['devices']
        mode = self.preferred_mode(devices, self.settings.get('mode'))
        color = self.settings['color']
        brightness = self.settings['brightness']
        speed = self.settings['speed']
        if spec['kind'] == 'zone':
            self.apply_zone(spec, color, mode, brightness, speed, quiet=True)
        else:
            self.apply_devices(devices, color, mode, brightness, speed,
                               target_key=target_key, quiet=True)

    def record_applied_configuration(self, color, target_key, mode, brightness,
                                     speed, zone_led_count=None):
        spec = self.target_specs.get(target_key)
        self.settings.update({
            'color': color.upper(),
            'target': target_key,
            'target_label': spec['label'] if spec else None,
            'target_kind': spec['kind'] if spec else None,
            'mode': mode,
            'brightness': brightness,
            'speed': speed,
            'restore_on_startup': True,
        })
        if zone_led_count is not None:
            self.settings['zone_led_count'] = zone_led_count
        self.save_settings()

    def make_targets(self):
        specs = {
            'all': {'key': 'all', 'kind': 'all', 'label': 'Todo o sistema',
                    'meta': f'{len(self.devices)} dispositivos' if self.detected else
                    'Procurando componentes…', 'devices': self.devices}
        }
        boards = [d for d in self.devices
                  if any(key in d['name'].lower() for key in ('asus', 'prime', 'motherboard'))]
        memories = [d for d in self.devices
                    if any(key in d['name'].lower() for key in ('corsair', 'memory', 'dram', 'ram'))]
        graphics = [d for d in self.devices
                    if any(key in d['name'].lower() for key in ('geforce', 'radeon', 'gpu', 'palit'))]
        assigned = {d['id'] for d in boards + memories + graphics}

        for device in boards:
            key = f"device:{device['id']}"
            specs[key] = {
                'key': key, 'kind': 'device', 'label': device['name'],
                'meta': 'Placa-mãe', 'devices': [device], 'device': device,
            }
            zones = device['zones']
            zone_index = next(
                (i for i, name in enumerate(zones)
                 if 'addressable' in name.lower() or 'argb' in name.lower()),
                None)
            if zone_index is not None:
                zone_key = f"zone:{device['id']}:{zone_index}"
                specs[zone_key] = {
                    'key': zone_key, 'kind': 'zone',
                    'label': 'Ventoinhas ARGB',
                    'meta': zones[zone_index], 'devices': [device],
                    'device': device, 'zone_index': zone_index,
                }

        if memories:
            key = 'memory:' + ','.join(d['id'] for d in memories)
            label = 'Memória Corsair' if any('corsair' in d['name'].lower() for d in memories) else 'Memória RGB'
            specs[key] = {
                'key': key, 'kind': 'group', 'label': label,
                'meta': f'{len(memories)} módulos', 'devices': memories,
            }
        if graphics:
            for device in graphics:
                key = f"device:{device['id']}"
                specs[key] = {
                    'key': key, 'kind': 'device', 'label': device['name'],
                    'meta': 'Placa de vídeo', 'devices': [device], 'device': device,
                }

        for device in self.devices:
            if device['id'] in assigned:
                continue
            key = f"device:{device['id']}"
            specs[key] = {
                'key': key, 'kind': 'device', 'label': device['name'],
                'meta': 'Dispositivo RGB', 'devices': [device], 'device': device,
            }

        order = ['all']
        for device in boards:
            order.append(f"device:{device['id']}")
            zone_index = next(
                (i for i, name in enumerate(device['zones'])
                 if 'addressable' in name.lower() or 'argb' in name.lower()),
                None)
            if zone_index is not None:
                order.append(f"zone:{device['id']}:{zone_index}")
        if memories:
            order.append('memory:' + ','.join(d['id'] for d in memories))
        order.extend(f"device:{d['id']}" for d in graphics)
        order.extend(k for k in specs if k not in order)
        return specs, order

    def rebuild_targets(self):
        specs, order = self.make_targets()
        self.target_specs = specs
        if self.selected_target not in specs and self.detected:
            self.selected_target = 'all'
        if not self.window:
            return
        self.target_buttons = {}
        for child in self.device_list.get_children():
            self.device_list.remove(child)
        self._updating_targets = True
        self.compact_target.remove_all()
        for key in order:
            spec = specs[key]
            button = Gtk.Button()
            button.set_relief(Gtk.ReliefStyle.NONE)
            self.css_control(button)
            button.get_style_context().add_class('device-row')
            row = Gtk.Box(spacing=9)
            dot = Gtk.Label(label='●')
            dot.get_style_context().add_class('device-dot')
            labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            name = Gtk.Label(label=spec['label'], xalign=0)
            name.get_style_context().add_class('device-name')
            name.set_line_wrap(True)
            meta = Gtk.Label(label=spec['meta'], xalign=0)
            meta.get_style_context().add_class('device-meta')
            labels.pack_start(name, False, False, 0)
            labels.pack_start(meta, False, False, 0)
            row.pack_start(dot, False, False, 0)
            row.pack_start(labels, True, True, 0)
            button.add(row)
            button.set_tooltip_text(f"{spec['label']} — {spec['meta']}")
            button.connect('clicked', lambda _button, target=key: self.select_target(target))
            self.device_list.pack_start(button, False, False, 0)
            self.target_buttons[key] = button
            self.compact_target.append(key, spec['label'])
        self.compact_target.set_active_id(self.selected_target)
        self._updating_targets = False
        self.update_target_view()
        self.device_list.show_all()
        if hasattr(self, 'empty_devices'):
            self.empty_devices.set_text(
                'Detectando componentes…' if not self.detected else
                'Nenhum componente RGB encontrado' if not self.devices else '')
            self.empty_devices.set_visible(not self.detected or not self.devices)

    def select_target(self, key):
        if key not in self.target_specs:
            return
        self.selected_target = key
        self._updating_targets = True
        if self.compact_target.get_active_id() != key:
            self.compact_target.set_active_id(key)
        self._updating_targets = False
        self.update_target_view()

    def compact_target_changed(self, combo):
        if not self._updating_targets and combo.get_active_id():
            self.select_target(combo.get_active_id())

    def current_spec(self):
        return self.target_specs.get(self.selected_target)

    def active_devices(self):
        spec = self.current_spec()
        return spec['devices'] if spec else []

    def update_target_view(self):
        spec = self.current_spec()
        if not spec or not self.window:
            return
        for key, button in self.target_buttons.items():
            context = button.get_style_context()
            if key == self.selected_target:
                context.add_class('selected')
            else:
                context.remove_class('selected')
        self.selected_target_label.set_text(spec['label'])
        self.mode_combo.remove_all()
        selected = spec['devices']
        modes = set(selected[0]['modes']) if selected else set()
        for device in selected[1:]:
            modes &= set(device['modes'])
        choices = sorted(modes, key=lambda mode: (mode.casefold() not in ('direct', 'static'), mode.casefold()))
        for mode in choices:
            self.mode_combo.append(mode, MODE_LABELS.get(mode.casefold(), mode))
        preferred = 'Direct' if 'Direct' in modes else ('Static' if 'Static' in modes else None)
        self.mode_combo.set_active_id(preferred or (choices[0] if choices else None))
        self.update_mode_sensitivity()
        is_zone = spec['kind'] == 'zone'
        self.zone_panel.set_visible(is_zone)
        self.apply_button.set_label('Aplicar nas ventoinhas' if is_zone else 'Aplicar iluminação')
        if is_zone:
            self.led_count.set_value(self.settings.get('zone_led_count', DEFAULT_ZONE_LEDS))
            self.zone_hint.set_text(
                f"{spec['meta']} · limite do conector: 500 LEDs. O controlador não informa quantos LEDs físicos estão ligados; use o total real para efeitos por LED.")
        self.set_sensitivity('rgb-primary', bool(selected))
        self.update_window_title()

    def update_window_title(self):
        if self.window:
            self.window.set_title(f"RGB Studio — {self.selected_target_label.get_text()}")

    def update_mode_sensitivity(self, *_):
        if not hasattr(self, 'brightness'):
            return
        mode = self.mode_combo.get_active_id()
        self.brightness.set_sensitive(bool(mode and mode != 'Off'))
        self.speed.set_sensitive(bool(mode and mode not in ('Direct', 'Static', 'Off')))

    def apply_current(self, *_):
        spec = self.current_spec()
        mode = self.mode_combo.get_active_id()
        brightness = round(self.brightness.get_value())
        speed = round(self.speed.get_value())
        if not spec or not mode:
            self.set_status('Nenhum modo disponível para esse alvo', 'error')
            return
        if spec['kind'] == 'zone':
            self.apply_zone(spec, self.selected_color, mode, brightness, speed)
        else:
            self.apply_devices(spec['devices'], self.selected_color, mode, brightness,
                               speed, target_key=self.selected_target)

    def scaled_color(self, color, brightness):
        values = [round(int(color[i:i+2], 16) * brightness / 100) for i in (1, 3, 5)]
        return ''.join(f'{value:02X}' for value in values)

    def apply_devices(self, devices, color, mode, brightness, speed, target_key=None,
                      quiet=False):
        if not devices:
            self.set_status('Nenhum dispositivo RGB detectado', 'error')
            return
        if not re.fullmatch(r'#[0-9A-F]{6}', color.upper()):
            self.set_status('Escolha um tom HEX válido', 'error')
            return
        applied_color = color.upper()
        self.sync_color(applied_color)
        target_ids = {device['id'] for device in devices}
        all_ids = {device['id'] for device in self.devices}
        target_key = self.target_for_devices(devices, target_key)
        spec = self.target_specs.get(target_key)
        if spec:
            target = spec['label']
        elif target_ids == all_ids:
            target = 'Todo o sistema'
        elif len(devices) == 1:
            target = devices[0]['name']
        else:
            target = f'{len(devices)} dispositivos'

        def job():
            args = []
            for device in devices:
                available = device['modes']
                chosen = mode if mode in available else next(
                    (name for name in ('Direct', 'Static') if name in available),
                    available[0] if available else None)
                if not chosen:
                    continue
                args.extend(['--device', device['id'], '--mode', chosen])
                if chosen in ('Direct', 'Static'):
                    args.extend(['--color', self.scaled_color(color, brightness)])
                elif chosen != 'Off':
                    args.extend(['--color', color.lstrip('#'), '--speed', str(speed),
                                 '--brightness', str(brightness)])
            if not args:
                raise RuntimeError('O modo selecionado não está disponível nesses dispositivos.')
            return self.command(args)

        def complete(_result):
            self.record_applied_configuration(
                applied_color, target_key, self.preferred_mode(devices, mode),
                brightness, speed)
            self.set_status(f"{target} · {applied_color} aplicado", 'good')
        self.submit(job, complete, quiet=quiet)

    def apply_zone(self, spec, color, mode, brightness, speed, quiet=False):
        if not re.fullmatch(r'#[0-9A-F]{6}', color.upper()):
            self.set_status('Escolha um tom HEX válido', 'error')
            return
        device = spec['device']
        zone = spec['zone_index']
        count = (self.led_count.get_value_as_int() if hasattr(self, 'led_count') else
                 self.settings.get('zone_led_count', DEFAULT_ZONE_LEDS))

        def job():
            args = ['--device', device['id'], '--zone', str(zone), '--size', str(count),
                    '--mode', mode]
            if mode in ('Direct', 'Static'):
                args += ['--color', self.scaled_color(color, brightness)]
            elif mode != 'Off':
                args += ['--color', color.lstrip('#'), '--speed', str(speed),
                         '--brightness', str(brightness)]
            return self.command(args)

        def complete(_result):
            self.record_applied_configuration(
                color, spec['key'], mode, brightness, speed, zone_led_count=count)
            self.set_status(f'Ventoinhas: tom aplicado na zona de {count} LEDs', 'good')
        self.submit(job, complete, quiet=quiet)

    def resize_zone(self, spec, count):
        device, zone = spec['device'], spec['zone_index']

        def job():
            return self.command(
                ['--device', device['id'], '--zone', str(zone), '--size', str(count)])

        def complete(_result):
            self.settings['zone_led_count'] = count
            self.save_settings()
            self.set_status(f'Zona ARGB configurada para {count} LEDs', 'good')
        self.submit(job, complete)

    def set_busy_controls(self, busy):
        if hasattr(self, 'apply_button'):
            for widget in self.action_controls:
                widget.set_sensitive(not busy)
            if hasattr(self, 'compact_target'):
                self.compact_target.set_sensitive(not busy)
            for button in getattr(self, 'target_buttons', {}).values():
                button.set_sensitive(not busy)

    def set_sensitivity(self, class_name, enabled):
        if hasattr(self, 'apply_button'):
            self.apply_button.set_sensitive(enabled and not self.busy)

    def set_status(self, message, kind='neutral'):
        if not hasattr(self, 'status_label'):
            return
        self.status_label.set_text(message)
        context = self.status_pill.get_style_context()
        for name in ('good', 'error'):
            context.remove_class(name)
        if kind in ('good', 'error'):
            context.add_class(kind)

    def sync_color(self, color):
        self.selected_color = color.upper()
        self._syncing_color = True
        if hasattr(self, 'hex_entry'):
            self.hex_entry.set_text(self.selected_color)
            self.hex_entry.get_style_context().remove_class('invalid')
            self.color_chip_provider.load_from_data(
                f'#rgb-color-chip {{ background-color: {self.selected_color}; border: 1px solid #718274; border-radius: 7px; }}'.encode())
            self.color_chip.get_accessible().set_name(
                f'Prévia da cor {self.selected_color}')
            _hue, saturation, _value = rgb_to_hsv(*(
                int(self.selected_color[i:i+2], 16) / 255 for i in (1, 3, 5)))
            self.color_saturation.set_value(saturation * 100)
            self.color_canvas.set_color(self.selected_color)
        self._syncing_color = False

    def color_field_changed(self, color):
        if not self._syncing_color:
            self.sync_color(color)

    def saturation_changed(self, slider):
        if self._syncing_color:
            return
        self.color_canvas.set_saturation(slider.get_value() / 100)
        self.color_canvas.emit_color()

    def hex_changed(self, entry):
        value = entry.get_text().strip()
        if self._syncing_color:
            return
        if re.fullmatch(r'#?[0-9A-Fa-f]{6}', value):
            self.sync_color('#' + value.lstrip('#'))
        else:
            entry.get_style_context().add_class('invalid')

    def choose_system_color(self, *_):
        dialog = Gtk.ColorChooserDialog(
            title='Escolher qualquer cor', transient_for=self.window, modal=True)
        rgba = Gdk.RGBA()
        rgba.parse(self.selected_color)
        dialog.set_rgba(rgba)

        def response(widget, result):
            if result == Gtk.ResponseType.OK:
                chosen = widget.get_rgba()
                color = '#%02X%02X%02X' % tuple(
                    round(value * 255) for value in (chosen.red, chosen.green, chosen.blue))
                self.sync_color(color)
            widget.destroy()
        dialog.connect('response', response)
        dialog.show_all()

    def css_class(self, widget, name):
        widget.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        widget.get_style_context().add_class(name)
        return widget

    def css_control(self, widget):
        widget.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        return widget

    def label(self, text, style=None, xalign=0):
        item = Gtk.Label(label=text, xalign=xalign)
        if style:
            item.get_style_context().add_class(style)
        return item

    def small_heading(self, text):
        return self.label(text.upper(), 'rgb-kicker')

    def build_color_panel(self):
        panel = self.css_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6), 'rgb-panel')
        panel.get_style_context().add_class('rgb-color-panel')
        top = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        top.pack_start(self.small_heading('ESPECTRO COMPLETO'), False, False, 0)
        top.pack_start(self.label('Arraste para escolher qualquer matiz', 'rgb-heading'), False, False, 0)
        panel.pack_start(top, False, False, 0)

        self.color_canvas = ColorCanvas(self.color_field_changed)
        panel.pack_start(self.color_canvas.widget, True, True, 0)
        self.color_saturation = self.scale_row(panel, 'Saturação do tom', 82)
        self.color_saturation.set_tooltip_text(
            'Reduza para tons suaves ou aumente para cores mais vivas')
        self.color_saturation.get_accessible().set_name('Saturação da cor')
        self.color_saturation.connect('value-changed', self.saturation_changed)

        values = Gtk.Box(spacing=8)
        self.color_chip = Gtk.EventBox()
        self.color_chip.set_name('rgb-color-chip')
        self.color_chip.set_size_request(36, 32)
        self.color_chip_provider = Gtk.CssProvider()
        self.color_chip.get_style_context().add_provider(
            self.color_chip_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.color_chip.get_accessible().set_name('Prévia da cor selecionada')
        values.pack_start(self.color_chip, False, False, 0)
        hex_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        hex_box.pack_start(self.small_heading('CÓDIGO HEX'), False, False, 0)
        self.hex_entry = self.css_control(Gtk.Entry())
        self.hex_entry.set_width_chars(9)
        self.hex_entry.set_max_length(7)
        self.hex_entry.get_accessible().set_name('Código hexadecimal da cor')
        self.hex_entry.set_text(self.selected_color)
        self.hex_entry.set_input_purpose(Gtk.InputPurpose.FREE_FORM)
        self.hex_entry.connect('changed', self.hex_changed)
        self.hex_entry.connect('activate', self.hex_changed)
        hex_box.pack_start(self.hex_entry, False, False, 0)
        values.pack_start(hex_box, False, False, 0)
        picker = self.css_class(Gtk.Button(label='Seletor do sistema'), 'rgb-secondary')
        picker.connect('clicked', self.choose_system_color)
        values.pack_end(picker, False, False, 0)
        panel.pack_start(values, False, False, 0)

        panel.pack_start(self.small_heading('PALETA · 18 MATIZES'), False, False, 0)
        swatches = self.css_class(Gtk.FlowBox(), 'rgb-palette')
        swatches.set_selection_mode(Gtk.SelectionMode.NONE)
        swatches.set_min_children_per_line(6)
        swatches.set_max_children_per_line(9)
        swatches.set_row_spacing(5)
        swatches.set_column_spacing(5)
        swatches.set_homogeneous(True)
        for name, color in SPECTRUM_SWATCHES:
            button = Gtk.Button(label='')
            button.set_size_request(29, 29)
            button.set_tooltip_text(f'{name} · {color}')
            button.get_accessible().set_name(f'{name}, {color}')
            button.get_style_context().add_class('rgb-swatch')
            self.css_control(button)
            swatch_provider = Gtk.CssProvider()
            swatch_provider.load_from_data(
                f'button {{ background-color: {color}; }} button:hover {{ border-color: #FFFFFF; }}'.encode())
            button.get_style_context().add_provider(
                swatch_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
            button.connect('clicked', lambda _button, value=color: self.sync_color(value))
            swatches.add(button)
        panel.pack_start(swatches, False, False, 0)
        return panel

    def scale_row(self, parent, title, value):
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        heading = Gtk.Box()
        heading.pack_start(self.label(title, 'rgb-muted'), True, True, 0)
        value_label = self.label(f'{value}%', 'rgb-number', xalign=1)
        heading.pack_end(value_label, False, False, 0)
        row.pack_start(heading, False, False, 0)
        scale = self.css_control(
            Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1))
        scale.get_accessible().set_name(title)
        scale.set_draw_value(False)
        scale.set_value(value)
        scale.set_can_focus(True)
        scale.connect('value-changed', lambda control: value_label.set_text(
            f'{round(control.get_value())}%'))
        row.pack_start(scale, False, False, 0)
        parent.pack_start(row, False, False, 0)
        return scale

    def build_effect_panel(self):
        panel = self.css_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15), 'rgb-panel')
        panel.pack_start(self.small_heading('EFEITO E INTENSIDADE'), False, False, 0)
        panel.pack_start(self.label('Modo de iluminação', 'rgb-muted'), False, False, 0)
        self.mode_combo = self.css_control(Gtk.ComboBoxText())
        self.mode_combo.get_accessible().set_name('Efeito de iluminação')
        self.mode_combo.set_hexpand(True)
        self.mode_combo.connect('changed', self.update_mode_sensitivity)
        panel.pack_start(self.mode_combo, False, False, 0)
        self.brightness = self.scale_row(panel, 'Brilho', 100)
        self.speed = self.scale_row(panel, 'Velocidade', 50)
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        panel.pack_start(separator, False, False, 2)
        panel.pack_start(self.small_heading('CENAS'), False, False, 0)
        scenes = Gtk.Box(spacing=7)
        save = self.css_class(Gtk.Button(label='Salvar'), 'rgb-secondary')
        save.connect('clicked', self.save_preset)
        load = self.css_class(Gtk.Button(label='Abrir'), 'rgb-secondary')
        load.connect('clicked', self.load_preset)
        scenes.pack_start(save, True, True, 0)
        scenes.pack_start(load, True, True, 0)
        panel.pack_start(scenes, False, False, 0)
        self.save_button, self.load_button = save, load
        return panel

    def build_zone_panel(self):
        panel = self.css_class(Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9), 'rgb-zone')
        heading = Gtk.Box(spacing=10)
        heading.pack_start(self.label('VENTOINHAS ARGB', 'rgb-heading'), True, True, 0)
        heading.pack_end(self.small_heading('ZONA DA PLACA-MÃE'), False, False, 0)
        panel.pack_start(heading, False, False, 0)
        self.zone_hint = self.label('', 'rgb-muted')
        self.zone_hint.set_line_wrap(True)
        panel.pack_start(self.zone_hint, False, False, 0)
        row = Gtk.Box(spacing=9)
        row.pack_start(self.label('LEDs configurados', 'rgb-muted'), False, False, 0)
        self.led_count = self.css_control(Gtk.SpinButton.new_with_range(1, 500, 1))
        self.led_count.set_value(self.settings.get('zone_led_count', DEFAULT_ZONE_LEDS))
        self.led_count.set_width_chars(5)
        self.led_count.get_accessible().set_name('Quantidade de LEDs da zona ARGB')
        row.pack_start(self.led_count, False, False, 0)
        self.zone_size_button = self.css_class(
            Gtk.Button(label='Configurar zona'), 'rgb-secondary')
        self.zone_size_button.connect('clicked', self.apply_zone_size)
        row.pack_start(self.zone_size_button, False, False, 0)
        row.pack_end(self.label('Até 500', 'rgb-muted'), False, False, 0)
        panel.pack_start(row, False, False, 0)
        return panel

    def build_ui(self):
        window = Gtk.Window(title='RGB Studio')
        self.window = window
        window.set_default_size(1060, 640)
        window.set_size_request(760, 620)
        window.set_position(Gtk.WindowPosition.CENTER)
        window.set_icon_from_file(str(BASE / 'rgb-panel.svg'))
        window.get_style_context().add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        window.get_style_context().add_class('rgb-window')
        window.connect('delete-event', lambda _window, _event: (window.hide(), True)[1])
        window.connect('size-allocate', self.adapt_layout)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        window.add(root)

        header = self.css_class(Gtk.Box(spacing=14), 'rgb-header')
        logo = Gtk.Label(label='●')
        logo.get_style_context().add_class('device-dot')
        header.pack_start(logo, False, False, 0)
        name_block = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name_block.pack_start(self.label('RGB STUDIO', 'rgb-wordmark'), False, False, 0)
        name_block.pack_start(self.label('Controle de iluminação', 'rgb-subtitle'), False, False, 0)
        header.pack_start(name_block, True, True, 0)
        compact_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        compact_box.set_size_request(220, -1)
        compact_box.pack_start(self.small_heading('COMPONENTE'), False, False, 0)
        self.compact_target = self.css_control(Gtk.ComboBoxText())
        self.compact_target.connect('changed', self.compact_target_changed)
        compact_box.pack_start(self.compact_target, False, False, 0)
        header.pack_end(compact_box, False, False, 0)
        self.compact_box = compact_box
        self.status_label = Gtk.Label(label='Localizando os componentes…')
        self.status_pill = self.css_class(Gtk.Box(), 'rgb-status')
        self.status_pill.pack_start(self.status_label, False, False, 0)
        header.pack_end(self.status_pill, False, False, 0)
        root.pack_start(header, False, False, 0)

        stage = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root.pack_start(stage, True, True, 0)
        self.nav_sidebar = self.css_class(
            Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10), 'rgb-sidebar')
        self.nav_sidebar.set_size_request(205, -1)
        self.nav_sidebar.pack_start(self.small_heading('COMPONENTES'), False, False, 5)
        self.device_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.nav_sidebar.pack_start(self.device_list, False, False, 0)
        self.empty_devices = self.label('Detectando componentes…', 'rgb-muted')
        self.empty_devices.set_line_wrap(True)
        self.nav_sidebar.pack_start(self.empty_devices, False, False, 4)
        self.nav_sidebar.pack_end(self.label('OpenRGB · local', 'rgb-muted'), False, False, 0)
        stage.pack_start(self.nav_sidebar, False, False, 0)

        content_scroll = Gtk.ScrolledWindow()
        content_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content_scroll.set_overlay_scrolling(False)
        self.content_scroll = content_scroll
        stage.pack_start(content_scroll, True, True, 0)
        content = self.css_class(
            Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=13), 'rgb-content')
        content_scroll.add(content)

        self.zone_panel = self.build_zone_panel()
        content.pack_start(self.zone_panel, False, False, 0)

        composer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=13)
        content.pack_start(composer, False, False, 0)
        self.composer = composer
        self.selected_target_label = self.label('Aguardando detecção…', 'rgb-muted')
        self.color_panel = self.build_color_panel()
        self.color_panel.set_size_request(400, -1)
        composer.pack_start(self.color_panel, True, True, 0)
        self.effect_panel = self.build_effect_panel()
        self.effect_panel.set_size_request(270, -1)
        composer.pack_start(self.effect_panel, False, False, 0)

        actions = self.css_class(Gtk.Box(spacing=9), 'rgb-footer')
        self.apply_button = self.css_class(
            Gtk.Button(label='Aplicar iluminação'), 'rgb-primary')
        self.apply_button.connect('clicked', self.apply_current)
        actions.pack_start(self.apply_button, False, False, 0)
        refresh = self.css_class(
            Gtk.Button(label='Redetectar componentes'), 'rgb-secondary')
        refresh.connect('clicked', self.refresh)
        actions.pack_start(refresh, False, False, 0)
        self.refresh_button = refresh
        root.pack_end(actions, False, False, 0)

        self.action_controls = [
            self.apply_button, self.zone_size_button, self.refresh_button,
            self.save_button, self.load_button,
        ]
        self.target_buttons = {}
        self.set_status('Localizando os componentes…', 'pending')
        self.sync_color(self.selected_color)
        self.rebuild_targets()
        window.show_all()
        self.content_scroll.get_vadjustment().set_value(
            self.content_scroll.get_vadjustment().get_lower())
        self.zone_panel.hide()
        self.adapt_layout(window, window.get_allocation())
        self.update_target_view()

    def adapt_layout(self, _window, allocation):
        narrow = allocation.width < 1030
        changed = self._laying_out != narrow
        self._laying_out = narrow
        if hasattr(self, 'nav_sidebar'):
            self.nav_sidebar.set_visible(not narrow)
            self.compact_box.set_visible(narrow)
            if changed:
                self.composer.set_orientation(
                    Gtk.Orientation.VERTICAL if narrow else Gtk.Orientation.HORIZONTAL)

    def apply_zone_size(self, *_):
        spec = self.current_spec()
        if not spec or spec['kind'] != 'zone':
            self.set_status('Selecione Ventoinhas ARGB para configurar essa zona', 'error')
            return
        self.resize_zone(spec, self.led_count.get_value_as_int())

    def save_preset(self, *_):
        dialog = Gtk.Dialog(title='Salvar cena', transient_for=self.window, modal=True)
        dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Salvar', Gtk.ResponseType.OK)
        area = dialog.get_content_area()
        area.set_spacing(10)
        area.set_border_width(15)
        area.pack_start(self.label('Nome para esta cor, efeito e componente:', 'rgb-muted'), False, False, 0)
        entry = Gtk.Entry()
        entry.set_placeholder_text('Ex.: Verde menta')
        area.pack_start(entry, False, False, 0)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            name = re.sub(r'[^\w -]', '', entry.get_text()).strip()
            if name:
                PRESETS.mkdir(parents=True, exist_ok=True)
                data = {
                    'color': self.selected_color,
                    'mode': self.mode_combo.get_active_id(),
                    'brightness': round(self.brightness.get_value()),
                    'speed': round(self.speed.get_value()),
                    'target': self.selected_target,
                }
                (PRESETS / (name + '.json')).write_text(
                    json.dumps(data, indent=2), encoding='utf-8')
                self.set_status(f'Cena “{name}” salva', 'good')
        dialog.destroy()

    def load_preset(self, *_):
        files = sorted(PRESETS.glob('*.json')) if PRESETS.exists() else []
        if not files:
            self.set_status('Ainda não há cenas salvas', 'neutral')
            return
        dialog = Gtk.Dialog(title='Abrir cena', transient_for=self.window, modal=True)
        dialog.add_buttons('Cancelar', Gtk.ResponseType.CANCEL, 'Abrir', Gtk.ResponseType.OK)
        combo = Gtk.ComboBoxText()
        for file in files:
            combo.append(str(file), file.stem)
        combo.set_active(0)
        dialog.get_content_area().pack_start(combo, True, True, 14)
        dialog.show_all()
        result = dialog.run()
        selected = combo.get_active_id()
        dialog.destroy()
        if result != Gtk.ResponseType.OK or not selected:
            return
        try:
            data = json.loads(Path(selected).read_text(encoding='utf-8'))
            color = data.get('color', '#39D353')
            if not re.fullmatch(r'#[0-9A-Fa-f]{6}', color):
                raise ValueError('A cena tem um código de cor inválido.')
            self.sync_color(color)
            self.brightness.set_value(data.get('brightness', 100))
            self.speed.set_value(data.get('speed', 50))
            if data.get('target') in self.target_specs:
                self.select_target(data['target'])
            if data.get('mode') and self.mode_combo.get_active_id() != data['mode']:
                self.mode_combo.set_active_id(data['mode'])
            self.apply_current()
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            self.set_status('Não foi possível abrir essa cena', 'error')
            dialog = Gtk.MessageDialog(
                transient_for=self.window, modal=True, message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE, text='Não consegui abrir essa cena')
            dialog.format_secondary_text(str(error))
            dialog.connect('response', lambda box, _response: box.destroy())
            dialog.show_all()

    def show_window(self, *_):
        if not self.window:
            self.build_ui()
        self.window.show_all()
        if self.current_spec() and self.current_spec()['kind'] != 'zone':
            self.zone_panel.hide()
        self.adapt_layout(self.window, self.window.get_allocation())
        self.window.present()

    def build_menu(self, status=None):
        menu = Gtk.Menu()
        header = Gtk.MenuItem(label='RGB Studio' + (' · ' + status if status else ''))
        header.set_sensitive(False)
        menu.append(header)
        open_item = Gtk.MenuItem(label='Abrir estúdio completo…')
        open_item.connect('activate', self.show_window)
        menu.append(open_item)
        quick_item = Gtk.MenuItem(label='Cores rápidas para tudo')
        submenu = Gtk.Menu()
        for label, color in QUICK:
            item = Gtk.MenuItem(label=label)
            item.connect('activate', lambda _item, value=color: self.apply_devices(
                self.devices, value, None, 100, 50))
            submenu.append(item)
        quick_item.set_submenu(submenu)
        menu.append(quick_item)
        if self.devices:
            for device in self.devices:
                item = Gtk.MenuItem(label=device['name'])
                submenu = Gtk.Menu()
                for label, color in QUICK:
                    option = Gtk.MenuItem(label=label)
                    option.connect('activate', lambda _item, value=color, target=device:
                                   self.apply_devices([target], value, None, 100, 50))
                    submenu.append(option)
                item.set_submenu(submenu)
                menu.append(item)
        menu.append(Gtk.SeparatorMenuItem())
        refresh = Gtk.MenuItem(label='Redetectar componentes')
        refresh.connect('activate', self.refresh)
        menu.append(refresh)
        quit_item = Gtk.MenuItem(label='Sair do RGB Studio')
        quit_item.connect('activate', Gtk.main_quit)
        menu.append(quit_item)
        menu.show_all()
        self.indicator.set_menu(menu)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = Panel()
    Gtk.main()
