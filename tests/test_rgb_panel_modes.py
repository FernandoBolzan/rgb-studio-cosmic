import re
import struct
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import rgb_panel


class PanelModeTests(unittest.TestCase):
    def setUp(self):
        self.panel = rgb_panel.Panel.__new__(rgb_panel.Panel)
        self.memory = {
            'id': '0',
            'name': 'Corsair Vengeance RGB Pro DDR4',
            'description': 'Corsair DRAM RGB Device',
            'type': 'DRAM',
            'modes': [
                'Direct', 'Custom', 'Color Shift', 'Color Pulse', 'Rainbow Wave',
                'Color Wave', 'Visor', 'Rain', 'Marquee', 'Rainbow', 'Sequential',
            ],
        }

    def test_device_parser_keeps_leds_and_ignores_malformed_quoted_lists(self):
        devices = rgb_panel.parse_devices(
            "0: Test GPU\n"
            "  Type: GPU\n"
            "  Modes: Direct 'broken quote\n"
            "  Zones: 'RGBW Zone' 'Single Color'\n"
            "  LEDs: 'Entire Zone' 'Entire Zone'\n")

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]['modes'], [])
        self.assertEqual(devices[0]['zones'], ['RGBW Zone', 'Single Color'])
        self.assertEqual(devices[0]['leds'], ['Entire Zone', 'Entire Zone'])

    def test_device_category_prefers_openrgb_type_to_vendor_name(self):
        self.assertEqual(rgb_panel.device_category({
            'name': 'ASUS GeForce RTX 3060', 'type': 'GPU'}), 'gpu')
        self.assertEqual(rgb_panel.device_category({
            'name': 'Corsair Vengeance RGB Pro', 'type': 'DRAM'}), 'memory')
        self.assertEqual(rgb_panel.device_category({
            'name': 'Palit PRIME Board', 'type': 'Motherboard'}), 'motherboard')
        self.assertIsNone(rgb_panel.device_category({
            'name': 'Corsair Harpoon RGB', 'type': 'Mouse'}))

    def test_target_groups_use_controller_type_without_misclassifying_devices(self):
        self.panel.devices = [
            {'id': '0', 'name': 'Corsair Vengeance DIMM', 'type': 'DRAM',
             'description': '', 'modes': ['Direct'], 'zones': [], 'leds': []},
            {'id': '1', 'name': 'ASUS GeForce RTX', 'type': 'GPU',
             'description': '', 'modes': ['Direct'], 'zones': [], 'leds': []},
            {'id': '2', 'name': 'Palit PRIME board', 'type': 'Motherboard',
             'description': '', 'modes': ['Direct'], 'zones': [], 'leds': []},
            {'id': '3', 'name': 'Corsair Harpoon RGB', 'type': 'Mouse',
             'description': '', 'modes': ['Direct'], 'zones': [], 'leds': []},
        ]
        self.panel.detected = True

        specs, order = self.panel.make_targets()

        self.assertIn('memory:0', specs)
        self.assertEqual(specs['device:1']['meta'], 'Placa de vídeo')
        self.assertEqual(specs['device:2']['meta'], 'Placa-mãe')
        self.assertEqual(specs['device:3']['meta'], 'Dispositivo RGB')
        self.assertEqual(order[:4], ['all', 'device:2', 'memory:0', 'device:1'])

    def test_load_settings_rejects_a_non_object_json_root(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'settings.json'
            config.write_text('[]', encoding='utf-8')
            with patch.object(rgb_panel, 'CONFIG', config):
                settings = self.panel.load_settings()

        self.assertIsNone(settings['target'])
        self.assertFalse(settings['restore_on_startup'])
        self.assertEqual(settings['brightness'], 100)

    def test_load_settings_preserves_valid_values_when_one_field_is_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'settings.json'
            config.write_text(
                '{"color":"#2EFF00","target":"device:3",'
                '"mode":"software:breathe","brightness":"bad",'
                '"speed":87,"restore_on_startup":true}',
                encoding='utf-8')
            with patch.object(rgb_panel, 'CONFIG', config):
                settings = self.panel.load_settings()

        self.assertEqual(settings['color'], '#2EFF00')
        self.assertEqual(settings['target'], 'device:3')
        self.assertEqual(settings['mode'], 'software:breathe')
        self.assertEqual(settings['brightness'], 100)
        self.assertEqual(settings['speed'], 87)
        self.assertTrue(settings['restore_on_startup'])

    def test_sdk_update_uses_one_persistent_packet_for_all_gpu_leds(self):
        class FakeSocket:
            def __init__(self, response):
                self.response = bytearray(response)
                self.sent = []

            def sendall(self, data):
                self.sent.append(data)

            def recv(self, size):
                chunk = bytes(self.response[:size])
                del self.response[:size]
                return chunk

            def settimeout(self, _timeout):
                return None

        ack = rgb_panel.OpenRGBFrameClient._packet(
            10, struct.pack('<II', 1050, 0), device_id=3)
        fake_socket = FakeSocket(ack)
        client = rgb_panel.OpenRGBFrameClient.__new__(rgb_panel.OpenRGBFrameClient)
        client.socket = fake_socket
        client.timeout = 1
        client.protocol_version = 6
        client.device_id = 3
        client.led_count = 2

        client.update_color('#12AB34')

        self.assertEqual(len(fake_socket.sent), 1)
        magic, device_id, packet_id, size = struct.unpack('<4sIII', fake_socket.sent[0][:16])
        self.assertEqual((magic, device_id, packet_id, size), (b'ORGB', 3, 1050, 14))
        self.assertEqual(
            fake_socket.sent[0][16:],
            struct.pack('<IH', 14, 2) + bytes.fromhex('12AB340012AB3400'))

    def test_sdk_controller_identity_parser_reads_name_and_type(self):
        name = b'Palit GeForce RTX 3060 LHR\0'
        data = struct.pack('<IiH', 10 + len(name), 2, len(name)) + name

        self.assertEqual(
            rgb_panel.OpenRGBFrameClient.parse_controller_identity(data),
            ('Palit GeForce RTX 3060 LHR', 2))

    def test_stale_gpu_connection_is_closed_after_effect_was_invalidated(self):
        callbacks = []
        self.panel.software_effect_generation = 0
        self.panel.software_animation = None
        self.panel.software_sdk_client = None
        self.panel.software_timer = None
        self.panel.system_sleeping = False
        self.panel.set_status = Mock()
        self.panel.submit = Mock(
            side_effect=lambda _job, done, quiet=False: callbacks.append(done))
        spec = {
            'key': 'device:3', 'label': 'Palit GPU',
            'devices': [{'id': '3', 'name': 'Palit GPU', 'type': 'GPU',
                         'modes': ['Direct'], 'leds': ['Entire Zone']}],
        }

        self.panel.start_software_effect(
            spec, '#2EFF00', 'software:breathe', 100, 60)
        self.panel.stop_software_effect()
        stale_client = Mock()

        self.assertFalse(callbacks[0](stale_client))
        stale_client.close.assert_called_once_with()
        self.assertIsNone(self.panel.software_animation)

    def test_all_corsair_modes_match_the_device_color_count(self):
        for mode in self.memory['modes']:
            with self.subTest(mode=mode):
                args = self.panel.device_effect_args(
                    self.memory, '#2EFF00', mode, brightness=100, speed=60)
                colors = args[args.index('--color') + 1].split(',') if '--color' in args else []
                capabilities = self.panel.mode_capabilities(self.memory, mode)
                self.assertEqual(len(colors), capabilities['color_count'])
                self.assertEqual(args[args.index('--mode') + 1], mode)

    def test_two_color_corsair_modes_derive_a_darker_secondary_color(self):
        for mode in ('Color Shift', 'Color Pulse', 'Color Wave', 'Visor', 'Rain'):
            with self.subTest(mode=mode):
                args = self.panel.device_effect_args(
                    self.memory, '#2EFF00', mode, brightness=100, speed=60)
                colors = args[args.index('--color') + 1].split(',')
                self.assertEqual(colors, ['2EFF00', '0E4C00'])

    def test_black_remains_black_in_modes_that_require_two_colors(self):
        args = self.panel.device_effect_args(
            self.memory, '#000000', 'Color Pulse', brightness=100, speed=60)
        self.assertEqual(args[args.index('--color') + 1], '000000,000000')

    def test_software_gpu_modes_generate_valid_changing_frame_colors(self):
        for mode, elapsed in (
            ('software:blink', (0.0, 0.8)),
            ('software:breathe', (0.0, 2.0)),
            ('software:rainbow', (0.0, 1.0)),
        ):
            with self.subTest(mode=mode):
                colors = [
                    self.panel.software_effect_color(mode, '#2EFF00', 100, 60, point)
                    for point in elapsed
                ]
                self.assertNotEqual(colors[0], colors[1])
                self.assertTrue(all(re.fullmatch(r'#[0-9A-F]{6}', color) for color in colors))

    def test_startup_restore_retries_when_devices_are_not_ready(self):
        self.panel.devices = []
        self.panel.settings = {'restore_on_startup': True}
        self.panel.startup_restore_completed = False
        self.panel.system_sleeping = False
        self.panel.schedule_startup_restore_retry = Mock()

        self.panel.restore_saved_configuration()

        self.panel.schedule_startup_restore_retry.assert_called_once_with()

    def test_startup_restore_waits_for_device_list_to_stabilize(self):
        self.panel.startup_restore_device_signature = None
        self.panel.startup_restore_stable_scans = 0
        gpu = {'id': '3', 'name': 'Palit GPU', 'type': 'GPU',
               'modes': ['Direct'], 'zones': ['RGB']}
        memory = {'id': '0', 'name': 'Corsair DIMM', 'type': 'DRAM',
                  'modes': ['Direct', 'Color Pulse'], 'zones': ['Memory']}

        self.assertFalse(self.panel.startup_device_list_is_stable([gpu]))
        self.assertFalse(self.panel.startup_device_list_is_stable([gpu, memory]))
        self.assertTrue(self.panel.startup_device_list_is_stable([gpu, memory]))

    def test_loaded_devices_retries_then_starts_restore_after_stable_scan(self):
        gpu = {'id': '3', 'name': 'Palit GPU', 'type': 'GPU',
               'modes': ['Direct'], 'zones': ['RGB'], 'leds': ['Entire Zone']}
        self.panel.devices = []
        self.panel.settings = {'restore_on_startup': True}
        self.panel.startup_restore_started = False
        self.panel.startup_restore_completed = False
        self.panel.startup_restore_device_signature = None
        self.panel.startup_restore_stable_scans = 0
        self.panel.rebuild_targets = Mock()
        self.panel.build_menu = Mock()
        self.panel.set_status = Mock()
        self.panel.schedule_startup_restore_retry = Mock()
        self.panel.restore_saved_configuration = Mock()

        self.panel.loaded([gpu])

        self.panel.schedule_startup_restore_retry.assert_called_once_with()
        self.panel.restore_saved_configuration.assert_not_called()

        self.panel.loaded([gpu])

        self.panel.restore_saved_configuration.assert_called_once_with()
        self.assertTrue(self.panel.startup_restore_started)

    def test_sleep_notification_pauses_effects_and_terminates_openrgb_clients(self):
        self.panel.system_sleeping = False
        self.panel.active_commands_lock = threading.Lock()
        self.panel.startup_restore_retry_timer = None
        process = Mock()
        process.poll.return_value = None
        self.panel.active_commands = {process}
        self.panel.stop_software_effect = Mock()

        self.panel.handle_sleep_state(True)

        self.assertTrue(self.panel.system_sleeping)
        self.panel.stop_software_effect.assert_called_once_with()
        process.terminate.assert_called_once_with()

    def test_logind_signal_dispatches_sleep_state_to_main_loop(self):
        parameters = rgb_panel.GLib.Variant('(b)', (True,))

        with patch.object(rgb_panel.GLib, 'idle_add') as idle_add:
            self.panel.on_prepare_for_sleep(
                None, 'org.freedesktop.login1', '/org/freedesktop/login1',
                'org.freedesktop.login1.Manager', 'PrepareForSleep', parameters)

        idle_add.assert_called_once_with(self.panel.handle_sleep_state, True)

    def test_resume_resets_restore_state_and_schedules_device_refresh(self):
        self.panel.system_sleeping = True
        self.panel.startup_restore_started = True
        self.panel.startup_restore_completed = True
        self.panel.startup_restore_attempts = 7
        self.panel.cancel_startup_restore_retry = Mock()

        with patch.object(rgb_panel.GLib, 'timeout_add_seconds', return_value=12) as timer:
            self.panel.handle_sleep_state(False)

        self.assertFalse(self.panel.system_sleeping)
        self.assertFalse(self.panel.startup_restore_started)
        self.assertFalse(self.panel.startup_restore_completed)
        self.assertEqual(self.panel.startup_restore_attempts, 0)
        self.panel.cancel_startup_restore_retry.assert_called_once_with()
        timer.assert_called_once_with(
            rgb_panel.RESUME_RESTORE_DELAY_SECONDS, self.panel.restore_after_resume)

    def test_resume_refresh_waits_for_pending_command_then_restarts_sdk(self):
        self.panel.system_sleeping = False
        self.panel.busy = True
        self.panel.software_frame_busy = False
        self.panel.stop_openrgb_server = Mock()
        self.panel.refresh = Mock()

        self.assertTrue(self.panel.restore_after_resume())
        self.panel.stop_openrgb_server.assert_not_called()
        self.panel.refresh.assert_not_called()

        self.panel.busy = False
        self.assertFalse(self.panel.restore_after_resume())
        self.panel.stop_openrgb_server.assert_called_once_with()
        self.panel.refresh.assert_called_once_with()

    def test_run_command_tracks_client_until_process_finishes(self):
        self.panel.active_commands = set()
        self.panel.active_commands_lock = threading.Lock()
        process = Mock()
        process.args = ['openrgb', '--noautoconnect', '--list-detailed']
        process.returncode = 0
        process.communicate.return_value = ('device list', '')

        with patch.object(rgb_panel.subprocess, 'Popen', return_value=process) as popen:
            result = self.panel.run_command(['--list-detailed'])

        self.assertIsInstance(result, subprocess.CompletedProcess)
        self.assertEqual(result.stdout, 'device list')
        self.assertEqual(self.panel.active_commands, set())
        popen.assert_called_once()

    def test_failed_startup_gpu_frame_schedules_restore_retry(self):
        animation = {'startup_restore': True, 'saved': False}
        self.panel.software_animation = animation
        self.panel.software_frame_busy = True
        self.panel.software_timer = None
        self.panel.startup_restore_completed = False
        self.panel.schedule_startup_restore_retry = Mock()
        self.panel.set_status = Mock()
        future = Mock()
        future.result.side_effect = RuntimeError('SDK unavailable')

        with patch.object(rgb_panel.logging, 'exception'):
            self.panel.finish_software_frame(animation, future, '#2EFF00', 100, 60)

        self.assertFalse(self.panel.software_frame_busy)
        self.assertIsNone(self.panel.software_animation)
        self.panel.schedule_startup_restore_retry.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
