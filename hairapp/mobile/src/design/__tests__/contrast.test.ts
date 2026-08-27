import { contrastRatio } from '../contrast';
import { contrastTargets, darkColors, lightColors } from '../tokens';

/**
 * El contraste no es una aspiración del documento de accesibilidad: es un
 * test. Un token que no llega al mínimo rompe el build.
 */
describe('contraste de los tokens', () => {
  const themes = { claro: lightColors, oscuro: darkColors };

  describe.each(Object.entries(themes))('tema %s', (_name, colors) => {
    it('el texto principal cumple AA sobre el fondo', () => {
      expect(contrastRatio(colors.ink, colors.background)).toBeGreaterThanOrEqual(
        contrastTargets.bodyTextMinimum,
      );
    });

    it('el texto principal cumple AA sobre las superficies', () => {
      for (const surface of [colors.surface, colors.surfaceRaised, colors.surfaceSunken]) {
        expect(contrastRatio(colors.ink, surface)).toBeGreaterThanOrEqual(
          contrastTargets.bodyTextMinimum,
        );
      }
    });

    it('el texto secundario cumple AA sobre el fondo', () => {
      expect(contrastRatio(colors.inkMuted, colors.background)).toBeGreaterThanOrEqual(
        contrastTargets.bodyTextMinimum,
      );
    });

    it('el texto sobre el acento cumple AA', () => {
      expect(contrastRatio(colors.accentInk, colors.accent)).toBeGreaterThanOrEqual(
        contrastTargets.bodyTextMinimum,
      );
    });

    it('el texto sobre aviso y alerta cumple AA', () => {
      expect(contrastRatio(colors.warnInk, colors.warn)).toBeGreaterThanOrEqual(
        contrastTargets.bodyTextMinimum,
      );
      expect(contrastRatio(colors.alertInk, colors.alert)).toBeGreaterThanOrEqual(
        contrastTargets.bodyTextMinimum,
      );
    });

    it('las líneas se distinguen del fondo', () => {
      expect(contrastRatio(colors.lineStrong, colors.background)).toBeGreaterThanOrEqual(1.2);
    });
  });

  it('los dos temas son de verdad distintos, no el mismo con otro nombre', () => {
    expect(lightColors.background).not.toBe(darkColors.background);
    expect(lightColors.ink).not.toBe(darkColors.ink);
    expect(contrastRatio(lightColors.background, '#000000')).toBeGreaterThan(
      contrastRatio(darkColors.background, '#000000'),
    );
  });
});
