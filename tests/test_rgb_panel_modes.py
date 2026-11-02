import re
import unittest

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


if __name__ == '__main__':
    unittest.main()
