# Histórico de alterações / Changelog

Este projeto segue o formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
This project follows the [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.

## [Unreleased] / Em desenvolvimento

_Nenhuma alteração registrada ainda. / No unreleased changes recorded yet._

## [v0.1.1] - 2026-11-03

### Correções

- A restauração aguarda dispositivos que demoram a aparecer no início do sistema e reaplica a configuração salva ao retornar da suspensão ou hibernação.
- Efeitos de GPU são pausados durante a suspensão; a conexão SDK é reiniciada e o efeito só é considerado restaurado depois do primeiro quadro aplicado.
- Efeitos animados da GPU usam uma conexão SDK persistente em vez de iniciar um processo OpenRGB por quadro; o controlador é validado pelo nome e tipo antes do envio.
- Conexões SDK pendentes são invalidadas durante a suspensão para evitar que um efeito antigo seja iniciado ao retornar.
- Listas de dispositivos e configurações JSON inválidas são tratadas sem derrubar a interface nem descartar outros campos válidos.
- A classificação de placa-mãe, memória e GPU prioriza o tipo de controlador informado pelo OpenRGB.

### Fixes

- Startup restoration now retries when devices appear late and reapplies saved lighting after the system resumes from sleep or hibernation.
- GPU effects pause during sleep; the SDK connection restarts on resume, and restoration is confirmed only after the first frame is applied.
- Animated GPU effects use a persistent SDK connection instead of starting an OpenRGB process for every frame; the controller name and type are checked before updates.
- Pending SDK connections are invalidated during sleep so a stale effect cannot start after resume.
- Invalid device lists and JSON settings are handled without crashing the interface or discarding other valid fields.
- Motherboard, memory, and GPU grouping now prefers the controller type reported by OpenRGB.

## [v0.1.0] - 2026-11-02

### Português

#### Destaques

- Painel RGB para COSMIC com seletor de espectro, paleta de cores, entrada HEX, controles de iluminação e cenas.
- Seleção de dispositivos individuais, grupos e zonas ARGB anunciadas pelo OpenRGB; contagem de LEDs salva por zona.
- Restauração da última configuração ao iniciar, incluindo alvo, efeito, cor, brilho, velocidade e contagem da zona.
- Controles mostram os modos comuns em grupos e preservam o nome de efeito anunciado por cada dispositivo.

#### Correções

- Modos Corsair Vengeance que exigem duas cores recebem uma segunda tonalidade mais escura derivada da cor escolhida.
- A GPU Palit pode usar Piscar, Respirar e Arco-íris por software quando o OpenRGB anuncia apenas Direct/Off.
- Cenas e preferências são gravadas atomicamente e mantêm a seleção de componente.

#### Compatibilidade

- Linux com COSMIC ou ambiente compatível com Ayatana/AppIndicator, Python 3, GTK 3, PyGObject e OpenRGB CLI.
- Os efeitos disponíveis dependem do controlador e da versão do OpenRGB. Efeitos por software na GPU exigem que o RGB Studio permaneça aberto.

### English

#### Highlights

- RGB control panel for COSMIC with a color spectrum, swatches, HEX input, lighting controls, and scenes.
- Targets individual devices, groups, and OpenRGB-reported ARGB zones; saves LED counts per zone.
- Restores the last configuration at startup, including target, effect, color, brightness, speed, and zone count.
- Shows shared modes for groups and preserves each device's advertised effect name.

#### Fixes

- Corsair Vengeance modes that require two colors now receive a darker secondary shade derived from the selected color.
- Palit GPUs can use software Blink, Breathe, and Rainbow when OpenRGB reports only Direct/Off.
- Scenes and preferences are written atomically and retain the selected component.

#### Compatibility

- Linux with COSMIC or an Ayatana/AppIndicator-compatible desktop, Python 3, GTK 3, PyGObject, and the OpenRGB CLI.
- Available effects depend on the controller and OpenRGB version. Software GPU effects require RGB Studio to remain running.
