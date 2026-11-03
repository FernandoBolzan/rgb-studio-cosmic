#!/usr/bin/python3
"""RGB Studio: desktop lighting controls for COSMIC, powered by OpenRGB."""
import atexit
import concurrent.futures
import json
import logging
import math
import os
import re
import shlex
import shutil
import signal
import socket
import struct
import subprocess
import threading
import time
from colorsys import hsv_to_rgb, rgb_to_hsv
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, Gdk, Gio, GLib, AyatanaAppIndicator3 as Indicator

BASE = Path.home() / '.local/share/rgb-panel'
BUNDLED_OPENRGB = BASE / 'openrgb/AppRun'
OPENRGB = (os.environ.get('RGB_PANEL_OPENRGB') or
           (str(BUNDLED_OPENRGB) if BUNDLED_OPENRGB.exists() else
            shutil.which('openrgb') or str(BUNDLED_OPENRGB)))
CONFIG = Path.home() / '.config/rgb-panel/settings.json'
PRESETS = Path.home() / '.config/rgb-panel/presets'
DEFAULT_ZONE_LEDS = 500
MAX_STARTUP_RESTORE_RETRIES = 24
STARTUP_RESTORE_RETRY_SECONDS = 5
RESUME_RESTORE_DELAY_SECONDS = 8
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
CORSAIR_DRAM_MODES = {
    'custom': {'fixed': True, 'color_count': 1, 'speed': False, 'brightness': True},
    'color shift': {'fixed': False, 'color_count': 2, 'speed': True, 'brightness': True},
    'color pulse': {'fixed': False, 'color_count': 2, 'speed': True, 'brightness': True},
    'rainbow wave': {'fixed': False, 'color_count': 0, 'speed': True, 'brightness': False},
    'color wave': {'fixed': False, 'color_count': 2, 'speed': True, 'brightness': True},
    'visor': {'fixed': False, 'color_count': 2, 'speed': True, 'brightness': True},
    'rain': {'fixed': False, 'color_count': 2, 'speed': True, 'brightness': True},
    'marquee': {'fixed': False, 'color_count': 1, 'speed': True, 'brightness': True},
    'rainbow': {'fixed': False, 'color_count': 0, 'speed': True, 'brightness': False},
    'sequential': {'fixed': False, 'color_count': 1, 'speed': True, 'brightness': True},
}
SOFTWARE_GPU_MODES = {
    'software:blink': 'Piscar (software)',
    'software:breathe': 'Respirar (software)',
    'software:rainbow': 'Arco-íris (software)',
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
            devices.append({'id': match[1], 'name': match[2], 'type': '',
                            'description': '', 'modes': [], 'zones': [], 'leds': []})
        elif devices and line.strip().startswith('Type:'):
            devices[-1]['type'] = line.split(':', 1)[1].strip()
        elif devices and line.strip().startswith('Description:'):
            devices[-1]['description'] = line.split(':', 1)[1].strip()
        elif devices and line.strip().startswith('Modes:'):
            try:
                devices[-1]['modes'] = [
                    mode.strip('[]')
                    for mode in shlex.split(line.split(':', 1)[1].strip())]
            except ValueError:
                logging.warning('Ignoring malformed OpenRGB mode list: %s', line.strip())
        elif devices and line.strip().startswith(('Zones:', 'LEDs:')):
            field = 'zones' if line.strip().startswith('Zones:') else 'leds'
            try:
                devices[-1][field] = shlex.split(line.split(':', 1)[1].strip())
            except ValueError:
                logging.warning('Ignoring malformed OpenRGB %s list: %s', field, line.strip())
    return devices


def device_category(device):
    """Return a known hardware category, preferring OpenRGB's controller type."""
    device_type = device.get('type', '').strip().casefold()
    categories = {
        'motherboard': 'motherboard',
        'dram': 'memory',
        'gpu': 'gpu',
    }
    if device_type in categories:
        return categories[device_type]
    if device_type and device_type not in ('unknown', 'other'):
        return None

    identity = (device.get('name', '') + ' ' +
                device.get('description', '')).casefold()
    if any(token in identity for token in ('geforce', 'radeon', 'graphics card', ' gpu')):
        return 'gpu'
    if any(token in identity for token in ('memory', 'dram', 'dimm', 'ddr3', 'ddr4', 'ddr5')) or re.search(r'\bram\b', identity):
        return 'memory'
    if any(token in identity for token in ('motherboard', 'mainboard', 'prime', 'tuf')):
        return 'motherboard'
    return None


class OpenRGBFrameClient:
    """Small persistent client for OpenRGB's documented TCP SDK protocol."""
    MAGIC = b'ORGB'
    MAX_PACKET_SIZE = 16 * 1024 * 1024
    MAX_PROTOCOL_VERSION = 6
    DEVICE_TYPES = {'motherboard': 0, 'dram': 1, 'gpu': 2}

    def __init__(self, device_index, led_count, host='127.0.0.1', port=6742,
                 timeout=2.0, expected_name=None, expected_type=None,
                 socket_factory=socket.create_connection):
        self.socket = socket_factory((host, port), timeout=timeout)
        self.socket.settimeout(timeout)
        self.timeout = timeout
        self.led_count = int(led_count)
        self.protocol_version = 0
        self.device_id = None
        self.expected_name = expected_name
        self.expected_type = expected_type
        if not 1 <= self.led_count <= 0xFFFF:
            self.close()
            raise ValueError('O OpenRGB informou uma quantidade inválida de LEDs para a GPU.')
        try:
            self._initialize(int(device_index))
        except Exception:
            self.close()
            raise

    @staticmethod
    def _packet(packet_id, payload=b'', device_id=0):
        return struct.pack('<4sIII', OpenRGBFrameClient.MAGIC, device_id,
                           packet_id, len(payload)) + payload

    def _send_packet(self, packet_id, payload=b'', device_id=0):
        self.socket.sendall(self._packet(packet_id, payload, device_id))

    def _read_exact(self, size):
        data = bytearray()
        while len(data) < size:
            chunk = self.socket.recv(size - len(data))
            if not chunk:
                raise ConnectionError('A conexão SDK do OpenRGB foi encerrada.')
            data.extend(chunk)
        return bytes(data)

    def _read_packet(self):
        header = self._read_exact(16)
        magic, device_id, packet_id, size = struct.unpack('<4sIII', header)
        if magic != self.MAGIC:
            raise ConnectionError('O servidor OpenRGB enviou um cabeçalho SDK inválido.')
        if size > self.MAX_PACKET_SIZE:
            raise ConnectionError(f'O servidor OpenRGB enviou um pacote grande demais ({size} bytes).')
        return device_id, packet_id, self._read_exact(size)

    def _wait_for_packet(self, packet_id, timeout=None):
        deadline = time.monotonic() + (self.timeout if timeout is None else timeout)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise socket.timeout(f'Tempo esgotado aguardando o pacote SDK {packet_id}.')
            self.socket.settimeout(remaining)
            _device_id, received_id, payload = self._read_packet()
            if received_id == 100:
                raise ConnectionError('A lista de dispositivos OpenRGB mudou durante o efeito.')
            if received_id == 10 and len(payload) == 8:
                acknowledged_id, status = struct.unpack('<II', payload)
                if status and acknowledged_id == packet_id:
                    raise RuntimeError(
                        f'O OpenRGB rejeitou o pacote SDK {packet_id} (status {status}).')
            if received_id == packet_id:
                return payload

    def _wait_for_ack(self, packet_id):
        if self.protocol_version < 6:
            return
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise socket.timeout(f'Tempo esgotado aguardando confirmação SDK {packet_id}.')
            self.socket.settimeout(remaining)
            _device_id, received_id, payload = self._read_packet()
            if received_id == 100:
                raise ConnectionError('A lista de dispositivos OpenRGB mudou durante o efeito.')
            if received_id != 10 or len(payload) != 8:
                continue
            acknowledged_id, status = struct.unpack('<II', payload)
            if acknowledged_id != packet_id:
                continue
            if status:
                raise RuntimeError(
                    f'O OpenRGB rejeitou o pacote SDK {packet_id} (status {status}).')
            self.socket.settimeout(self.timeout)
            return

    @staticmethod
    def parse_controller_identity(data):
        if len(data) < 10:
            raise ConnectionError('Dados de controlador OpenRGB incompletos.')
        data_size = struct.unpack_from('<I', data)[0]
        device_type = struct.unpack_from('<i', data, 4)[0]
        name_size = struct.unpack_from('<H', data, 8)[0]
        if data_size != len(data) or name_size < 1 or 10 + name_size > len(data):
            raise ConnectionError('Dados de controlador OpenRGB inválidos.')
        name = data[10:10 + name_size].decode('utf-8', errors='replace').rstrip('\0')
        return name, device_type

    def _controller_identity(self, device_id):
        request_data = (struct.pack('<I', self.protocol_version)
                        if self.protocol_version else b'')
        self._send_packet(1, request_data, device_id)
        return self.parse_controller_identity(self._wait_for_packet(1))

    def _initialize(self, device_index):
        self._send_packet(50, b'RGB Studio\0')
        self._send_packet(40, struct.pack('<I', self.MAX_PROTOCOL_VERSION))
        try:
            version_data = self._wait_for_packet(40, timeout=0.5)
            if len(version_data) != 4:
                raise ConnectionError('Resposta de versão SDK do OpenRGB inválida.')
            self.protocol_version = min(
                struct.unpack('<I', version_data)[0], self.MAX_PROTOCOL_VERSION)
        except socket.timeout:
            # OpenRGB protocol 0 predates version negotiation and sends no reply.
            self.protocol_version = 0

        if self.protocol_version >= 6:
            self._send_packet(52, struct.pack('<I', (1 << 0) | (1 << 16)))
            self._wait_for_packet(53)

        self._send_packet(0)
        count_data = self._wait_for_packet(0)
        if len(count_data) < 4:
            raise ConnectionError('Resposta de quantidade de dispositivos OpenRGB inválida.')
        controller_count = struct.unpack_from('<I', count_data)[0]
        if controller_count > 4096:
            raise ConnectionError('O servidor OpenRGB informou uma quantidade inválida de dispositivos.')
        expected_size = 4 + (controller_count * 4 if self.protocol_version >= 6 else 0)
        if len(count_data) != expected_size:
            raise ConnectionError('A resposta de dispositivos OpenRGB está incompleta.')
        if not 0 <= device_index < controller_count:
            raise RuntimeError(
                f'A GPU selecionada não existe no servidor SDK do OpenRGB (índice {device_index}).')
        controller_ids = (
            struct.unpack_from('<' + 'I' * controller_count, count_data, 4)
            if self.protocol_version >= 6 else tuple(range(controller_count)))
        selected_device_id = controller_ids[device_index]
        if self.expected_name is not None:
            expected_type = self.DEVICE_TYPES.get(
                str(self.expected_type or '').casefold())
            candidate_indexes = [device_index] + [
                index for index in range(controller_count) if index != device_index]
            matching_ids = []
            for index in candidate_indexes:
                candidate_id = controller_ids[index]
                name, device_type = self._controller_identity(candidate_id)
                if (name == self.expected_name and
                        (expected_type is None or device_type == expected_type)):
                    matching_ids.append(candidate_id)
                    if index == device_index:
                        break
            if not matching_ids:
                raise RuntimeError(
                    f"A GPU {self.expected_name} não foi encontrada no servidor SDK do OpenRGB.")
            if selected_device_id not in matching_ids:
                if len(matching_ids) != 1:
                    raise RuntimeError(
                        f"Há mais de um controlador chamado {self.expected_name}; "
                        'não posso escolher a GPU com segurança.')
                selected_device_id = matching_ids[0]
        self.device_id = selected_device_id
        self.socket.settimeout(self.timeout)

    def set_custom_mode(self):
        self._send_packet(1100, device_id=self.device_id)
        self._wait_for_ack(1100)

    def update_color(self, color):
        rgb = bytes(int(color[index:index + 2], 16) for index in (1, 3, 5))
        one_color = rgb + b'\0'
        color_data = struct.pack('<H', self.led_count) + one_color * self.led_count
        payload = struct.pack('<I', 4 + len(color_data)) + color_data
        self._send_packet(1050, payload, self.device_id)
        self._wait_for_ack(1050)

    def close(self):
        connection = getattr(self, 'socket', None)
        self.socket = None
        if connection:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()


def write_json_atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    try:
        temporary.write_text(json.dumps(data, indent=2), encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


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
        self.active_commands = set()
        self.active_commands_lock = threading.Lock()
        self.openrgb_server_process = None
        self.sdk_server_active = False
        self.software_sdk_client = None
        self.software_effect_generation = 0
        self.software_animation = None
        self.software_timer = None
        self.software_frame_busy = False
        atexit.register(self.stop_openrgb_server)
        self.devices = []
        self.target_specs = {}
        self.selected_target = 'all'
        self.busy = False
        self.startup_restore_started = False
        self.startup_restore_completed = False
        self.startup_restore_attempts = 0
        self.startup_restore_device_signature = None
        self.startup_restore_stable_scans = 0
        self.startup_restore_retry_timer = None
        self.system_sleeping = False
        self.login1_connection = None
        self.sleep_signal_subscription = None
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
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self.quit_app)
        self.watch_system_sleep()
        self.refresh()

    def load_settings(self):
        defaults = {
            'zone_led_count': DEFAULT_ZONE_LEDS,
            'zone_led_counts': {},
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
            if not isinstance(data, dict):
                logging.warning('Ignoring RGB Studio settings: the JSON root is not an object')
                return defaults

            def bounded_int(key, default, minimum=0, maximum=100):
                try:
                    return max(minimum, min(maximum, int(data.get(key, default))))
                except (TypeError, ValueError, OverflowError):
                    return default

            count = bounded_int('zone_led_count', DEFAULT_ZONE_LEDS, 1, 500)
            color = str(data.get('color', '#39D353')).upper()
            if not re.fullmatch(r'#[0-9A-F]{6}', color):
                color = '#39D353'
            target = data.get('target')
            target_label = data.get('target_label')
            target_kind = data.get('target_kind')
            mode = data.get('mode')
            raw_zone_counts = data.get('zone_led_counts', {})
            zone_led_counts = {}
            if isinstance(raw_zone_counts, dict):
                for key, value in raw_zone_counts.items():
                    if not isinstance(key, str):
                        continue
                    try:
                        zone_led_counts[key] = max(1, min(500, int(value)))
                    except (TypeError, ValueError, OverflowError):
                        continue
            restore_on_startup = data.get('restore_on_startup', 'color' in data)
            if not isinstance(restore_on_startup, bool):
                restore_on_startup = 'color' in data
            return {
                'zone_led_count': count,
                'zone_led_counts': zone_led_counts,
                'color': color,
                'target': target if isinstance(target, str) else None,
                'target_label': target_label if isinstance(target_label, str) else None,
                'target_kind': target_kind if isinstance(target_kind, str) else None,
                'mode': mode if isinstance(mode, str) else None,
                'brightness': bounded_int('brightness', 100),
                'speed': bounded_int('speed', 50),
                # Old settings files contain a color written only after applying it.
                'restore_on_startup': restore_on_startup,
            }
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return defaults

    def save_settings(self):
        write_json_atomic(CONFIG, self.settings)

    def run_command(self, args, sdk_client=False):
        command = ([OPENRGB, '--client', '127.0.0.1:6742'] if sdk_client else
                   [OPENRGB, '--noautoconnect'])
        with self.active_commands_lock:
            process = subprocess.Popen(
                [*command, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True)
            self.active_commands.add(process)
        try:
            stdout, stderr = process.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise
        finally:
            with self.active_commands_lock:
                self.active_commands.discard(process)
        return subprocess.CompletedProcess(
            process.args, process.returncode, stdout, stderr)

    def watch_system_sleep(self):
        try:
            self.login1_connection = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
            self.sleep_signal_subscription = self.login1_connection.signal_subscribe(
                'org.freedesktop.login1', 'org.freedesktop.login1.Manager',
                'PrepareForSleep', '/org/freedesktop/login1', None,
                Gio.DBusSignalFlags.NONE, self.on_prepare_for_sleep)
            logging.info('Watching system suspend/resume notifications via logind')
        except GLib.Error:
            logging.exception('Could not watch system suspend/resume notifications')

    def on_prepare_for_sleep(self, _connection, _sender, _path, _interface, _signal,
                             parameters):
        GLib.idle_add(self.handle_sleep_state, bool(parameters.unpack()[0]))

    def handle_sleep_state(self, entering_sleep):
        if entering_sleep:
            if self.system_sleeping:
                return False
            self.system_sleeping = True
            logging.info('System is suspending; pausing RGB Studio effects')
            self.stop_software_effect()
            self.cancel_startup_restore_retry()
            self.cancel_active_commands()
            return False

        if not self.system_sleeping:
            return False
        self.system_sleeping = False
        self.startup_restore_started = False
        self.startup_restore_completed = False
        self.startup_restore_attempts = 0
        self.startup_restore_device_signature = None
        self.startup_restore_stable_scans = 0
        self.cancel_startup_restore_retry()
        logging.info('System resumed; RGB Studio will rediscover devices and restore settings')
        GLib.timeout_add_seconds(RESUME_RESTORE_DELAY_SECONDS, self.restore_after_resume)
        return False

    def restore_after_resume(self):
        if self.system_sleeping:
            return False
        if self.busy or self.software_frame_busy:
            logging.info('Waiting for an in-flight OpenRGB command before resume restore')
            return True
        self.stop_software_effect()
        self.stop_openrgb_server()
        self.sdk_server_active = False
        self.refresh()
        return False

    def cancel_active_commands(self):
        with self.active_commands_lock:
            processes = list(self.active_commands)
        for process in processes:
            if process.poll() is None:
                process.terminate()

    def resize_mode_colors(self, args, mode_name, count):
        adjusted = []
        active_mode = None
        index = 0
        while index < len(args):
            item = args[index]
            if item == '--device':
                active_mode = None
            if item == '--mode' and index + 1 < len(args):
                active_mode = args[index + 1]
            if (item == '--color' and index + 1 < len(args) and active_mode and
                    active_mode.casefold() == mode_name.casefold()):
                if count > 0:
                    colors = args[index + 1].split(',')
                    adjusted.extend([item, ','.join(self.colors_for_mode(colors[0], count))])
                index += 2
                continue
            adjusted.append(item)
            index += 1
        return adjusted

    def command(self, args, sdk_client=None):
        if sdk_client is None:
            sdk_client = getattr(self, 'sdk_server_active', False)
        result = self.run_command(args, sdk_client=sdk_client)
        combined = result.stdout + result.stderr
        color_count = re.search(
            r'Wrong number of colors specified for mode\s+([^\r\n]+)\s*'
            r'[\r\n]+Please provide between\s+(\d+)\s+and\s+(\d+)\s+colors?',
            combined, re.IGNORECASE)
        corrected = args
        if color_count and not result.returncode:
            mode_name = color_count.group(1).strip()
            minimum = int(color_count.group(2))
            corrected = self.resize_mode_colors(args, mode_name, minimum)
            if corrected != args:
                result = self.run_command(corrected, sdk_client=sdk_client)
                combined = result.stdout + result.stderr
        errors = [line.strip() for line in combined.splitlines()
                  if re.match(r'^\s*error:', line, re.IGNORECASE) or
                  re.match(r'^\s*wrong number of colors specified for mode',
                           line, re.IGNORECASE)]
        if color_count and corrected != args and not result.returncode and not errors:
            logging.info('Retried OpenRGB mode %r with %s colors',
                         color_count.group(1).strip(), minimum)
        if result.returncode or 'Connection attempt failed' in combined or errors:
            message = '\n'.join(errors) or result.stderr or result.stdout or \
                'O OpenRGB não conseguiu aplicar o ajuste'
            raise RuntimeError(message[-1800:])
        return result.stdout

    def is_corsair_dram(self, device):
        identity = (device.get('name', '') + ' ' +
                    device.get('description', '')).casefold()
        return device.get('type', '').casefold() == 'dram' and 'corsair' in identity

    def mode_capabilities(self, device, mode):
        normalized = mode.casefold() if mode else ''
        if normalized == 'off':
            return {'fixed': False, 'color_count': 0, 'speed': False, 'brightness': False}
        if normalized in ('direct', 'static'):
            return {'fixed': True, 'color_count': 1, 'speed': False, 'brightness': True}
        if self.is_corsair_dram(device) and normalized in CORSAIR_DRAM_MODES:
            return CORSAIR_DRAM_MODES[normalized]
        return {'fixed': False, 'color_count': None, 'speed': True, 'brightness': True}

    def colors_for_mode(self, color, count):
        base = color.upper().lstrip('#')
        if count <= 0:
            return []
        colors = [base]
        rgb = [int(base[index:index + 2], 16) for index in (0, 2, 4)]
        for index in range(1, count):
            shade = ''.join(f'{round(channel * (0.3 ** index)):02X}' for channel in rgb)
            colors.append(shade)
        return colors

    def device_effect_args(self, device, color, mode, brightness, speed,
                           zone=None, zone_size=None):
        chosen = self.mode_for_device(device, mode)
        if not chosen:
            raise RuntimeError(f"{device['name']} não informa modos de iluminação.")
        args = ['--device', device['id']]
        if zone is not None:
            args.extend(['--zone', str(zone)])
            if zone_size is not None:
                args.extend(['--size', str(zone_size)])
        args.extend(['--mode', chosen])
        capabilities = self.mode_capabilities(device, chosen)
        if capabilities['fixed']:
            args.extend(['--color', self.scaled_color(color, brightness)])
            return args
        color_count = capabilities['color_count']
        if color_count is None:
            color_count = 1
        colors = self.colors_for_mode(color, color_count)
        if colors:
            args.extend(['--color', ','.join(colors)])
        if capabilities['speed']:
            args.extend(['--speed', str(speed)])
        if capabilities['brightness']:
            args.extend(['--brightness', str(brightness)])
        return args

    def ensure_sdk_server(self, expected_device=None):
        process = getattr(self, 'openrgb_server_process', None)
        if process and process.poll() is not None:
            self.openrgb_server_process = None
            process = None
        self.sdk_server_active = False

        def probe_server():
            result = self.run_command(['--list-detailed'], sdk_client=True)
            output = result.stdout + result.stderr
            if (result.returncode or 'Connection attempt failed' in output or
                    re.search(r'^\s*error:', output, re.IGNORECASE | re.MULTILINE)):
                return False
            if expected_device is None:
                return bool(parse_devices(result.stdout))
            return any(
                device['id'] == expected_device['id'] and
                device['name'] == expected_device['name'] and
                device['type'].casefold() == expected_device.get('type', '').casefold()
                for device in parse_devices(result.stdout))

        try:
            with socket.create_connection(('127.0.0.1', 6742), timeout=0.3):
                if probe_server():
                    self.sdk_server_active = True
                    return True
        except OSError:
            if process is None:
                self.openrgb_server_process = subprocess.Popen(
                    [OPENRGB, '--noautoconnect', '--server'],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, start_new_session=True)
                process = self.openrgb_server_process

        for _attempt in range(50):
            if process and process.poll() is not None:
                self.openrgb_server_process = None
                raise RuntimeError('O servidor SDK do OpenRGB encerrou antes de iniciar.')
            try:
                with socket.create_connection(('127.0.0.1', 6742), timeout=0.3):
                    if probe_server():
                        self.sdk_server_active = True
                        return True
            except OSError:
                pass
            time.sleep(0.2)
        if process:
            self.stop_openrgb_server()
        if expected_device:
            raise RuntimeError(
                f"A GPU {expected_device['name']} não apareceu no servidor SDK do OpenRGB.")
        raise RuntimeError('Não consegui iniciar o servidor SDK do OpenRGB na porta 6742.')

    def stop_openrgb_server(self):
        process = getattr(self, 'openrgb_server_process', None)
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        self.openrgb_server_process = None
        self.sdk_server_active = False

    def connect_software_device(self, device):
        logging.info('Connecting to the OpenRGB SDK for GPU %s (%s)',
                     device['name'], device['id'])
        self.ensure_sdk_server(device)
        leds = device.get('leds') or []
        if not leds:
            raise RuntimeError(
                f"O OpenRGB não informou os LEDs da GPU {device['name']}; "
                'não posso iniciar o efeito com segurança.')
        client = OpenRGBFrameClient(
            device['id'], len(leds), expected_name=device['name'],
            expected_type=device.get('type'))
        try:
            client.set_custom_mode()
        except Exception:
            client.close()
            raise
        logging.info('OpenRGB SDK selected GPU %s as controller %s',
                     device['name'], client.device_id)
        return client

    def stop_software_sdk_client(self):
        client = getattr(self, 'software_sdk_client', None)
        self.software_sdk_client = None
        if client:
            client.close()

    def send_software_frame(self, color):
        client = self.software_sdk_client
        if client is None:
            raise RuntimeError('A conexão SDK do efeito de GPU não está ativa.')
        client.update_color(color)

    def stop_software_effect(self):
        self.software_effect_generation = getattr(
            self, 'software_effect_generation', 0) + 1
        self.software_animation = None
        self.stop_software_sdk_client()
        timer = getattr(self, 'software_timer', None)
        if timer:
            GLib.source_remove(timer)
            self.software_timer = None

    def quit_app(self, *_):
        self.stop_software_effect()
        self.cancel_active_commands()
        self.stop_openrgb_server()
        if self.login1_connection and self.sleep_signal_subscription:
            self.login1_connection.signal_unsubscribe(self.sleep_signal_subscription)
        Gtk.main_quit()

    def software_effect_color(self, mode, color, brightness, speed, elapsed):
        if mode == 'software:blink':
            period = 2.4 - (speed / 100) * 2.0
            factor = brightness / 100 if elapsed % period < period / 2 else 0
            return '#' + self.scaled_color(color, round(factor * 100))
        if mode == 'software:breathe':
            period = 8.0 - (speed / 100) * 6.0
            factor = (0.08 + 0.92 * (1 - math.cos(2 * math.pi * elapsed / period)) / 2)
            return '#' + self.scaled_color(color, round(factor * brightness))
        hue = (elapsed * (0.05 + speed * 0.0045)) % 1.0
        rgb = hsv_to_rgb(hue, 1.0, brightness / 100)
        return '#%02X%02X%02X' % tuple(round(channel * 255) for channel in rgb)

    def start_software_effect(self, spec, color, mode, brightness, speed, quiet=False):
        devices = spec['devices']
        if (len(devices) != 1 or devices[0].get('type', '').casefold() != 'gpu' or
                'direct' not in {item.casefold() for item in devices[0]['modes']}):
            self.set_status('Efeito por software disponível para GPUs com modo Direct', 'error')
            if quiet:
                self.schedule_startup_restore_retry()
            return
        self.stop_software_effect()
        generation = self.software_effect_generation
        device = devices[0]

        def ready(client):
            if (generation != self.software_effect_generation or
                    self.system_sleeping):
                client.close()
                return False
            self.software_sdk_client = client
            self.software_animation = {
                'device': device,
                'target_key': spec['key'],
                'target': spec['label'],
                'mode': mode,
                'color': color.upper(),
                'brightness': brightness,
                'speed': speed,
                'started': time.monotonic(),
                'saved': False,
                'startup_restore': quiet,
            }
            self.software_timer = GLib.timeout_add(150, self.software_effect_frame)
            self.set_status(f"{spec['label']} · {SOFTWARE_GPU_MODES[mode]} ativo", 'good')
            self.build_menu('Efeito de GPU ativo')

        self.submit(lambda: self.connect_software_device(device), ready, quiet=quiet)

    def software_effect_frame(self):
        animation = self.software_animation
        if not animation:
            self.software_timer = None
            return False
        if self.busy or self.software_frame_busy:
            return True

        brightness = (round(self.brightness.get_value()) if hasattr(self, 'brightness')
                      else animation['brightness'])
        speed = (round(self.speed.get_value()) if hasattr(self, 'speed')
                 else animation['speed'])
        color = self.selected_color if hasattr(self, 'selected_color') else animation['color']
        frame_color = self.software_effect_color(
            animation['mode'], color, brightness, speed,
            time.monotonic() - animation['started'])
        self.software_frame_busy = True
        future = self.pool.submit(self.send_software_frame, frame_color)
        future.add_done_callback(
            lambda result: GLib.idle_add(self.finish_software_frame, animation, result,
                                         color, brightness, speed))
        return True

    def finish_software_frame(self, animation, future, color, brightness, speed):
        self.software_frame_busy = False
        if self.software_animation is not animation:
            return False
        try:
            future.result()
        except Exception:
            logging.exception('GPU software effect failed')
            self.stop_software_effect()
            self.set_status('Falha no efeito de GPU', 'error')
            if animation.get('startup_restore'):
                self.schedule_startup_restore_retry()
            return False
        if not animation['saved']:
            self.record_applied_configuration(
                color, animation['target_key'], animation['mode'], brightness, speed)
            animation['saved'] = True
            logging.info('Started GPU software effect %s on %s',
                         animation['mode'], animation['target'])
        if animation.get('startup_restore'):
            self.startup_restore_completed = True
            self.cancel_startup_restore_retry()
        return False

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
            done_result = done(future.result())
            if quiet:
                if (self.software_animation and
                        self.software_animation.get('startup_restore')):
                    menu_status = 'Restaurando efeito da GPU…'
                elif self.system_sleeping:
                    menu_status = 'Aguardando o retorno do sistema…'
                elif self.startup_restore_started:
                    self.startup_restore_completed = True
                    self.cancel_startup_restore_retry()
                    menu_status = 'Configuração reaplicada'
                elif done_result is False:
                    menu_status = 'Aguardando restauração…'
        except Exception as error:
            logging.exception('RGB action failed')
            self.set_status('Falha ao aplicar', 'error')
            if quiet:
                if self.startup_restore_attempts < MAX_STARTUP_RESTORE_RETRIES:
                    self.schedule_startup_restore_retry()
                    menu_status = 'Tentando restaurar…'
                else:
                    logging.error('Could not restore saved RGB settings after %s retries',
                                  self.startup_restore_attempts)
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
        self.startup_restore_retry_timer = None
        if self.system_sleeping or self.startup_restore_completed:
            return False
        if self.busy:
            self.schedule_startup_restore_retry()
            return False
        self.startup_restore_started = False
        self.refresh()
        return False

    def schedule_startup_restore_retry(self):
        if (self.startup_restore_completed or self.system_sleeping or
                not self.settings.get('restore_on_startup')):
            return
        if self.startup_restore_attempts >= MAX_STARTUP_RESTORE_RETRIES:
            logging.error('Could not restore saved RGB settings after %s retries',
                          self.startup_restore_attempts)
            return
        if self.startup_restore_retry_timer:
            return
        self.startup_restore_attempts += 1
        self.startup_restore_retry_timer = GLib.timeout_add_seconds(
            STARTUP_RESTORE_RETRY_SECONDS, self.retry_startup_restore)

    def cancel_startup_restore_retry(self):
        timer = self.startup_restore_retry_timer
        if timer:
            GLib.source_remove(timer)
            self.startup_restore_retry_timer = None

    def refresh(self, *_):
        self.submit(
            lambda: parse_devices(self.command(['--list-detailed'])),
            self.loaded)

    def loaded(self, devices):
        self.devices = devices
        self.detected = True
        logging.info('OpenRGB scan found %s devices', len(devices))
        self.rebuild_targets()
        self.build_menu(f'{len(devices)} dispositivos')
        self.set_status(
            f'{len(devices)} dispositivos encontrados' if devices else 'Nenhum dispositivo RGB detectado',
            'good' if devices else 'error')
        if (self.settings.get('restore_on_startup') and
                not self.startup_restore_started and
                not self.startup_restore_completed):
            if not devices:
                self.startup_restore_device_signature = None
                self.startup_restore_stable_scans = 0
                logging.info('Waiting for OpenRGB devices before restoring saved settings')
                self.schedule_startup_restore_retry()
                return
            if not self.startup_device_list_is_stable(devices):
                logging.info('Waiting for a stable OpenRGB device list (%s/2 scans)',
                             self.startup_restore_stable_scans)
                self.schedule_startup_restore_retry()
                return
            self.startup_restore_started = True
            logging.info('Restoring saved RGB target %r in mode %r',
                         self.settings.get('target'), self.settings.get('mode'))
            self.restore_saved_configuration()

    def startup_device_list_is_stable(self, devices):
        signature = tuple(sorted((
            str(device.get('id', '')),
            str(device.get('name', '')),
            str(device.get('type', '')).casefold(),
            tuple(sorted((str(mode) for mode in device.get('modes', [])),
                         key=str.casefold)),
            tuple(str(zone) for zone in device.get('zones', [])),
        ) for device in devices))
        if signature != self.startup_restore_device_signature:
            self.startup_restore_device_signature = signature
            self.startup_restore_stable_scans = 1
            return False
        self.startup_restore_stable_scans += 1
        return self.startup_restore_stable_scans >= 2

    def common_modes(self, devices):
        if not devices:
            return {}
        common = {mode.casefold(): mode for mode in devices[0]['modes']}
        for device in devices[1:]:
            supported = {mode.casefold() for mode in device['modes']}
            common = {key: mode for key, mode in common.items() if key in supported}
        return common

    def mode_for_device(self, device, requested=None):
        modes = {mode.casefold(): mode for mode in device['modes']}
        if requested is not None:
            resolved = modes.get(requested.casefold())
            if resolved is None:
                raise ValueError(
                    f"{device['name']} não oferece o modo de iluminação “{requested}”.")
            return resolved
        return (modes.get('direct') or modes.get('static') or
                next(iter(device['modes']), None))

    def preferred_mode(self, devices, requested=None):
        common = self.common_modes(devices)
        if requested is not None and requested.casefold() in common:
            return common[requested.casefold()]
        for preferred in ('direct', 'static'):
            if preferred in common:
                return common[preferred]
        return next((common[key] for key in sorted(common)), None)

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
        if self.startup_restore_completed or self.system_sleeping:
            return
        if not self.devices:
            self.schedule_startup_restore_retry()
            return

        target_key = self.settings.get('target') or 'all'
        spec = self.find_saved_target(
            target_key, self.settings.get('target_label'),
            self.settings.get('target_kind'))
        if not spec:
            logging.warning('Saved RGB target %r is unavailable; skipping startup restore',
                            target_key)
            self.set_status('O componente salvo não foi encontrado', 'error')
            self.schedule_startup_restore_retry()
            return
        target_key = spec['key']

        devices = spec['devices']
        requested_mode = self.settings.get('mode')
        if requested_mode in SOFTWARE_GPU_MODES:
            self.start_software_effect(
                spec, self.settings['color'], requested_mode,
                self.settings['brightness'], self.settings['speed'], quiet=True)
            return
        common = self.common_modes(devices)
        if requested_mode and requested_mode.casefold() not in common:
            logging.warning('Saved RGB mode %r is unavailable for target %r',
                            requested_mode, target_key)
            self.set_status('O efeito salvo não está disponível neste componente', 'error')
            self.schedule_startup_restore_retry()
            return
        mode = self.preferred_mode(devices, requested_mode)
        color = self.settings['color']
        brightness = self.settings['brightness']
        speed = self.settings['speed']
        if spec['kind'] == 'zone':
            self.apply_zone(spec, color, mode, brightness, speed, quiet=True)
        else:
            self.apply_devices(devices, color, mode, brightness, speed,
                               target_key=target_key, quiet=True)

    def find_saved_target(self, key=None, label=None, kind=None):
        keyed = self.target_specs.get(key) if key else None
        if label:
            matches = [candidate for candidate in self.target_specs.values()
                       if candidate['label'] == label and
                       (kind is None or candidate['kind'] == kind)]
            if len(matches) == 1:
                return matches[0]
            if matches:
                return keyed if keyed in matches else None
            # Older releases named every ARGB zone "Ventoinhas ARGB".
            if label == 'Ventoinhas ARGB' and kind == 'zone':
                if keyed and keyed['kind'] == 'zone':
                    return keyed
                zones = [candidate for candidate in self.target_specs.values()
                         if candidate['kind'] == 'zone']
                return zones[0] if len(zones) == 1 else None
            if keyed and keyed['label'] == label and (kind is None or keyed['kind'] == kind):
                return keyed
            return None
        return keyed

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
            self.settings.setdefault('zone_led_counts', {})[target_key] = zone_led_count
        self.save_settings()

    def zone_led_count_for(self, spec):
        counts = self.settings.get('zone_led_counts', {})
        value = counts.get(spec['key']) if isinstance(counts, dict) else None
        if value is None:
            value = self.settings.get('zone_led_count', DEFAULT_ZONE_LEDS)
        return max(1, min(500, int(value)))

    def make_targets(self):
        specs = {
            'all': {'key': 'all', 'kind': 'all', 'label': 'Todo o sistema',
                    'meta': f'{len(self.devices)} dispositivos' if self.detected else
                    'Procurando componentes…', 'devices': self.devices}
        }
        boards = [d for d in self.devices if device_category(d) == 'motherboard']
        memories = [d for d in self.devices if device_category(d) == 'memory']
        graphics = [d for d in self.devices if device_category(d) == 'gpu']
        for device in boards:
            key = f"device:{device['id']}"
            specs[key] = {
                'key': key, 'kind': 'device', 'label': device['name'],
                'meta': 'Placa-mãe', 'devices': [device], 'device': device,
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
            key = f"device:{device['id']}"
            if key not in specs:
                specs[key] = {
                    'key': key, 'kind': 'device', 'label': device['name'],
                    'meta': ('Módulo de memória' if device in memories else
                             'Placa de vídeo' if device in graphics else
                             'Dispositivo RGB'),
                    'devices': [device], 'device': device,
                }
            for zone_index, name in enumerate(device['zones']):
                if not any(token in name.casefold() for token in ('addressable', 'argb')):
                    continue
                zone_key = f"zone:{device['id']}:{zone_index}"
                specs[zone_key] = {
                    'key': zone_key, 'kind': 'zone',
                    'label': f"{device['name']} · {name}",
                    'meta': 'Zona ARGB endereçável', 'devices': [device],
                    'device': device, 'zone_index': zone_index,
                }

        order = ['all']
        for device in boards:
            order.append(f"device:{device['id']}")
        if memories:
            order.append('memory:' + ','.join(d['id'] for d in memories))
        order.extend(f"device:{d['id']}" for d in graphics)
        for device in self.devices:
            device_key = f"device:{device['id']}"
            if device_key in specs and device_key not in order:
                order.append(device_key)
            for zone_index, name in enumerate(device['zones']):
                zone_key = f"zone:{device['id']}:{zone_index}"
                if zone_key in specs:
                    order.append(zone_key)
        order.extend(k for k in specs if k not in order)
        return specs, order

    def rebuild_targets(self):
        specs, order = self.make_targets()
        self.target_specs = specs
        if (self.detected and
                (self.selected_target not in specs or
                 self.selected_target == self.settings.get('target'))):
            saved = self.find_saved_target(
                self.settings.get('target'), self.settings.get('target_label'),
                self.settings.get('target_kind'))
            self.selected_target = saved['key'] if saved else 'all'
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
        if key != self.selected_target:
            self.stop_software_effect()
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
        modes = self.common_modes(selected)
        choices = sorted(
            modes.values(),
            key=lambda mode: (mode.casefold() not in ('direct', 'static'), mode.casefold()))
        for mode in choices:
            self.mode_combo.append(mode, MODE_LABELS.get(mode.casefold(), mode))
        software_target = (
            len(selected) == 1 and selected[0].get('type', '').casefold() == 'gpu' and
            'direct' in {mode.casefold() for mode in selected[0]['modes']})
        if software_target:
            for mode_id, label in SOFTWARE_GPU_MODES.items():
                self.mode_combo.append(mode_id, label)
        saved_mode = (self.settings.get('mode')
                      if self.selected_target == self.settings.get('target') else None)
        preferred = (saved_mode if software_target and saved_mode in SOFTWARE_GPU_MODES else
                     self.preferred_mode(selected, saved_mode))
        self.mode_combo.set_active_id(preferred or (choices[0] if choices else None))
        self.mode_combo.set_tooltip_text(
            'Mostrando apenas efeitos compatíveis com todos os dispositivos deste alvo.'
            if len(selected) > 1 else
            'Efeitos e controles disponíveis para este dispositivo, conforme o OpenRGB.')
        if not choices:
            self._mode_hint_base = 'O OpenRGB não anunciou modos para este alvo.'
        elif len(selected) > 1:
            self._mode_hint_base = (
                f"Exibindo efeitos comuns aos {len(selected)} dispositivos deste alvo. "
                'Selecione um componente para ver os efeitos específicos.')
        else:
            self._mode_hint_base = 'Efeitos anunciados pelo OpenRGB para este componente.'
        if software_target:
            self._mode_hint_base += ' Efeitos por software exigem que o RGB Studio permaneça ativo.'
        self.mode_hint.set_text(self._mode_hint_base)
        self.update_mode_sensitivity()
        is_zone = spec['kind'] == 'zone'
        self.zone_panel.set_visible(is_zone)
        self.apply_button.set_label('Aplicar na zona ARGB' if is_zone else 'Aplicar iluminação')
        if is_zone:
            self.led_count.set_value(self.zone_led_count_for(spec))
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
        capabilities = [self.mode_capabilities(device, mode)
                        for device in self.active_devices()]
        self.brightness.set_sensitive(bool(capabilities and
                                           all(item['brightness'] for item in capabilities)))
        self.speed.set_sensitive(bool(capabilities and
                                      all(item['speed'] for item in capabilities)))
        if hasattr(self, 'mode_hint') and hasattr(self, '_mode_hint_base'):
            hint = self._mode_hint_base
            if any((item['color_count'] or 0) > 1 for item in capabilities):
                hint += ' Este efeito usa uma segunda cor mais escura, derivada da cor escolhida.'
            elif mode in SOFTWARE_GPU_MODES:
                hint += ' O efeito é animado pelo RGB Studio e enviado pela conexão SDK do OpenRGB.'
            self.mode_hint.set_text(hint)

    def apply_current(self, *_):
        spec = self.current_spec()
        mode = self.mode_combo.get_active_id()
        brightness = round(self.brightness.get_value())
        speed = round(self.speed.get_value())
        if not spec or not mode:
            self.set_status('Nenhum modo disponível para esse alvo', 'error')
            return
        if mode in SOFTWARE_GPU_MODES:
            self.start_software_effect(spec, self.selected_color, mode, brightness, speed)
            return
        self.stop_software_effect()
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
        self.stop_software_effect()
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
                args.extend(self.device_effect_args(
                    device, color, mode, brightness, speed))
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
        self.stop_software_effect()
        device = spec['device']
        zone = spec['zone_index']
        count = (self.led_count.get_value_as_int()
                 if hasattr(self, 'led_count') and self.selected_target == spec['key']
                 else self.zone_led_count_for(spec))

        def job():
            args = self.device_effect_args(
                device, color, mode, brightness, speed, zone=zone, zone_size=count)
            return self.command(args)

        def complete(_result):
            self.record_applied_configuration(
                color, spec['key'], self.mode_for_device(device, mode), brightness,
                speed, zone_led_count=count)
            self.set_status(f'Zona ARGB configurada para {count} LEDs', 'good')
        self.submit(job, complete, quiet=quiet)

    def resize_zone(self, spec, count):
        device, zone = spec['device'], spec['zone_index']

        def job():
            return self.command(
                ['--device', device['id'], '--zone', str(zone), '--size', str(count)])

        def complete(_result):
            self.settings['zone_led_count'] = count
            self.settings.setdefault('zone_led_counts', {})[spec['key']] = count
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
        self.mode_hint = self.label('', 'rgb-muted')
        self.mode_hint.set_line_wrap(True)
        panel.pack_start(self.mode_hint, False, False, 0)
        self.brightness = self.scale_row(
            panel, 'Brilho', self.settings.get('brightness', 100))
        self.speed = self.scale_row(panel, 'Velocidade', self.settings.get('speed', 50))
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
        heading.pack_start(self.label('ZONA ARGB', 'rgb-heading'), True, True, 0)
        heading.pack_end(self.small_heading('ZONA ENDEREÇÁVEL'), False, False, 0)
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
            self.set_status('Selecione uma zona ARGB para configurar', 'error')
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
                    'target_label': (self.current_spec()['label']
                                     if self.current_spec() else None),
                    'target_kind': (self.current_spec()['kind']
                                    if self.current_spec() else None),
                }
                if self.current_spec() and self.current_spec()['kind'] == 'zone':
                    data['zone_led_count'] = self.led_count.get_value_as_int()
                write_json_atomic(PRESETS / (name + '.json'), data)
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
            if not isinstance(data, dict):
                raise ValueError('O arquivo da cena não contém um objeto válido.')
            color = data.get('color', '#39D353')
            if not re.fullmatch(r'#[0-9A-Fa-f]{6}', color):
                raise ValueError('A cena tem um código de cor inválido.')

            target = None
            if data.get('target'):
                target = self.find_saved_target(
                    data.get('target'), data.get('target_label'), data.get('target_kind'))
                if not target:
                    raise ValueError('O componente salvo nesta cena não foi encontrado.')
            else:
                target = self.current_spec()
            if not target:
                raise ValueError('Selecione um componente antes de abrir esta cena.')

            saved_mode = data.get('mode')
            modes = self.common_modes(target['devices'])
            supports_software_mode = (
                saved_mode in SOFTWARE_GPU_MODES and len(target['devices']) == 1 and
                target['devices'][0].get('type', '').casefold() == 'gpu' and
                'direct' in {item.casefold() for item in target['devices'][0]['modes']})
            if supports_software_mode:
                mode = saved_mode
            elif saved_mode:
                mode = modes.get(str(saved_mode).casefold())
                if not mode:
                    raise ValueError(
                        f"O efeito “{saved_mode}” não está disponível em {target['label']}.")
            else:
                mode = self.preferred_mode(target['devices'])
            if not mode:
                raise ValueError(f"{target['label']} não informa efeitos de iluminação.")

            try:
                brightness = max(0, min(100, int(data.get('brightness', 100))))
                speed = max(0, min(100, int(data.get('speed', 50))))
                zone_led_count = max(
                    1, min(500, int(data.get(
                        'zone_led_count', self.zone_led_count_for(target)))))
            except (TypeError, ValueError, OverflowError):
                raise ValueError('Brilho, velocidade ou quantidade de LEDs inválida na cena.')

            self.select_target(target['key'])
            self.sync_color(color)
            self.brightness.set_value(brightness)
            self.speed.set_value(speed)
            if target['kind'] == 'zone':
                self.led_count.set_value(zone_led_count)
            self.mode_combo.set_active_id(mode)
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
        quit_item.connect('activate', self.quit_app)
        menu.append(quit_item)
        menu.show_all()
        self.indicator.set_menu(menu)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = Panel()
    Gtk.main()
