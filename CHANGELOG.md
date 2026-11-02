# Histórico de alterações / Changelog

## Em desenvolvimento / Unreleased

- Corrige os modos Corsair de duas cores e adiciona Piscar, Respirar e Arco-íris por software para GPUs; aguarda a detecção completa da GPU pelo servidor SDK.
- Fixes two-color Corsair modes and adds software Blink, Breathe, and Rainbow effects for GPUs; waits for GPU discovery by the SDK server.
- Normaliza nomes de modos, valida o efeito em cada dispositivo e informa quando um modo salvo não está mais disponível.
- Lista todas as zonas ARGB endereçáveis anunciadas pelo OpenRGB; salva a contagem de LEDs por zona e preserva alvo e contagem nas cenas.
- Lists every addressable ARGB zone reported by OpenRGB, stores each zone's LED count separately, and preserves target and count in scenes.
- Normalizes mode names, validates effects per device, and reports when a saved mode is no longer available.
- Reaplica ao iniciar a última iluminação configurada e salva alvo, efeito, brilho e velocidade junto da cor e da quantidade de LEDs.
- Reapplies the last lighting configuration at startup and saves the target, effect, brightness, and speed alongside the color and LED count.
- Publicação inicial do RGB Studio para COSMIC com seletor de espectro, entrada HEX, paleta, controles de iluminação e cenas.
- Initial public snapshot of RGB Studio for COSMIC with spectrum picker, HEX input, color swatches, lighting controls, and scenes.
- Add current overview and ARGB-zone screenshots to both localized READMEs.
