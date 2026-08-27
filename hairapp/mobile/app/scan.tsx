import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { Pressable, View } from 'react-native';

import { ApiError } from '@/api/client';
import { useApi } from '@/api/provider';
import type { PhotoQuality, ScanResult } from '@/api/types';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Screen } from '@/components/Screen';
import { Stack } from '@/components/Stack';
import { ErrorState, LoadingState } from '@/components/StateViews';
import { Text } from '@/components/Text';
import { WhyThis } from '@/components/WhyThis';
import { useTheme } from '@/design/theme';
import { t, tKey } from '@/i18n';

/**
 * Flujo de scan (A3).
 *
 * Cosas que esta pantalla hace y la mayoría de apps del sector no:
 *  - pide permiso explícito para analizar fotos y funciona sin él,
 *  - dice qué zonas cubre cada ángulo **antes** de hacer la foto,
 *  - valida la calidad foto a foto y pide repetir solo la que salió mal,
 *  - dice cuándo no está analizando la imagen, en vez de aparentar que sí,
 *  - no guarda nada en el perfil hasta que la persona lo confirma.
 */
export default function ScanFlow(): React.ReactElement {
  const theme = useTheme();
  const router = useRouter();
  const api = useApi();
  const queryClient = useQueryClient();

  const [scanId, setScanId] = useState<string | null>(null);
  const [qualityByAngle, setQualityByAngle] = useState<Record<string, PhotoQuality>>({});
  const [result, setResult] = useState<ScanResult | null>(null);
  const [consentError, setConsentError] = useState(false);

  const angles = useQuery({
    queryKey: ['scan-angles'],
    queryFn: () => api.scans.requiredAngles(),
  });

  const grantConsent = useMutation({
    mutationFn: () => api.auth.setConsents([{ purpose: 'photo_processing', granted: true }]),
    onSuccess: () => {
      setConsentError(false);
      void queryClient.invalidateQueries({ queryKey: ['me'] });
    },
  });

  const startScan = useMutation({
    mutationFn: () => api.scans.create(),
    onSuccess: (data) => setScanId(data.id),
    onError: (error) => {
      if (error instanceof ApiError && error.isConsentRequired) {
        setConsentError(true);
      }
    },
  });

  const upload = useMutation({
    mutationFn: async ({ angle, uri }: { angle: string; uri: string }) => {
      if (!scanId) {
        throw new Error('scan no iniciado');
      }
      const form = new FormData();
      form.append('angle', angle);
      form.append('face_cropped', 'false');
      form.append('file', {
        uri,
        name: `${angle}.jpg`,
        type: 'image/jpeg',
      } as unknown as Blob);
      return api.scans.uploadPhoto(scanId, form);
    },
    onSuccess: (quality) => {
      setQualityByAngle((current) => ({ ...current, [quality.angle]: quality }));
    },
  });

  const analyse = useMutation({
    mutationFn: () => {
      if (!scanId) {
        throw new Error('scan no iniciado');
      }
      return api.scans.analyse(scanId);
    },
    onSuccess: setResult,
  });

  const confirm = useMutation({
    mutationFn: () => {
      if (!scanId) {
        throw new Error('scan no iniciado');
      }
      return api.scans.confirm(scanId);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['zones'] });
      void queryClient.invalidateQueries({ queryKey: ['profile'] });
      router.replace('/(tabs)/map');
    },
  });

  async function pickPhoto(angle: string): Promise<void> {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    const picked = permission.granted
      ? await ImagePicker.launchCameraAsync({ quality: 0.9 })
      : await ImagePicker.launchImageLibraryAsync({ quality: 0.9 });
    const asset = picked.assets?.[0];
    if (!picked.canceled && asset) {
      upload.mutate({ angle, uri: asset.uri });
    }
  }

  if (consentError) {
    return (
      <Screen>
        <Card>
          <Stack gap="lg">
            <Text variant="title" tone="strong" accessibilityRole="header">
              {t('scan.consentTitle')}
            </Text>
            <Text variant="body" tone="muted">
              {t('scan.consentBody')}
            </Text>
            <Button
              label={t('scan.consentAccept')}
              loading={grantConsent.isPending}
              onPress={() =>
                grantConsent.mutate(undefined, { onSuccess: () => startScan.mutate() })
              }
            />
            <Button label={t('common.notNow')} variant="ghost" onPress={() => router.back()} />
          </Stack>
        </Card>
      </Screen>
    );
  }

  if (angles.isLoading) {
    return (
      <Screen>
        <LoadingState />
      </Screen>
    );
  }

  const uploaded = Object.keys(qualityByAngle).length;
  const toRetake = Object.values(qualityByAngle).filter((q) => q.must_retake);

  return (
    <Screen>
      <Stack gap="lg">
        <Stack gap="xs">
          <Text variant="title" tone="strong" accessibilityRole="header">
            {t('scan.title')}
          </Text>
          <Text variant="callout" tone="muted">
            {t('scan.intro')}
          </Text>
        </Stack>

        {!scanId ? (
          <Button
            label={t('common.continue')}
            loading={startScan.isPending}
            onPress={() => startScan.mutate()}
          />
        ) : null}

        {scanId
          ? (angles.data?.angles ?? []).map((angle) => {
              const quality = qualityByAngle[angle.angle];
              return (
                <Card key={angle.angle} tone={quality?.must_retake ? 'warn' : 'default'}>
                  <Stack gap="sm">
                    <View
                      style={{
                        flexDirection: 'row',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <Text variant="subheading">{tKey(angle.label_key)}</Text>
                      <Text variant="caption" tone={angle.required ? 'accent' : 'faint'}>
                        {angle.required ? t('scan.required') : t('scan.optionalAngle')}
                      </Text>
                    </View>

                    {/* Se dice de antemano qué zonas cubre esta foto. */}
                    <Text variant="caption" tone="muted">
                      {t('scan.covers', { count: angle.covers_zones.length })}
                    </Text>

                    {quality ? (
                      <Stack gap="xs">
                        {quality.issues.map((issue) => (
                          <Text
                            key={issue.code}
                            variant="caption"
                            tone={issue.blocking ? 'warn' : 'faint'}
                          >
                            {tKey(`scan.quality.${issue.code}`)}
                          </Text>
                        ))}
                        {quality.issues.length === 0 ? (
                          <Text variant="caption" tone="accent">
                            {t('scan.allGood')}
                          </Text>
                        ) : null}
                      </Stack>
                    ) : null}

                    <Pressable
                      onPress={() => void pickPhoto(angle.angle)}
                      accessibilityRole="button"
                      style={{
                        minHeight: theme.touchTarget.comfortable,
                        borderRadius: theme.radius.md,
                        borderWidth: 1,
                        borderStyle: 'dashed',
                        borderColor: theme.colors.lineStrong,
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Text variant="caption" tone="accent">
                        {quality ? t('common.retry') : t('common.continue')}
                      </Text>
                    </Pressable>
                  </Stack>
                </Card>
              );
            })
          : null}

        {upload.isError ? (
          <ErrorState
            message={upload.error instanceof Error ? upload.error.message : t('error.generic')}
          />
        ) : null}

        {toRetake.length > 0 ? (
          <Text variant="caption" tone="warn">
            {t('scan.retakeOnly', { count: toRetake.length })}
          </Text>
        ) : null}

        {scanId && uploaded > 0 && toRetake.length === 0 && !result ? (
          <Button
            label={t('scan.analysing')}
            loading={analyse.isPending}
            onPress={() => analyse.mutate()}
          />
        ) : null}

        {result ? <ScanReview result={result} onConfirm={() => confirm.mutate()} /> : null}
      </Stack>
    </Screen>
  );
}

function ScanReview({
  result,
  onConfirm,
}: {
  result: ScanResult;
  onConfirm: () => void;
}): React.ReactElement {
  const zonesObserved = result.observations.filter((o) => o.observed).length;
  const zonesMissing = result.observations.filter((o) => !o.observed);

  return (
    <Card>
      <Stack gap="lg">
        <Text variant="subheading">{t('scan.confirmTitle')}</Text>
        <Text variant="callout" tone="muted">
          {t('scan.confirmBody')}
        </Text>

        {/* Honestidad sobre el modelo ausente: no se aparenta un análisis
            de imagen que hoy no ocurre (docs/07-SCANNER-PIPELINE.md). */}
        {!result.used_image_analysis ? (
          <Card tone="warn">
            <Text variant="callout">{t('scan.noVisionModel')}</Text>
          </Card>
        ) : null}

        <Text variant="caption" tone="muted">
          {`${zonesObserved} / ${result.observations.length}`}
        </Text>

        {zonesMissing.length > 0 ? (
          <Stack gap="xxs">
            {zonesMissing.slice(0, 6).map((observation) => (
              <Text key={observation.zone} variant="caption" tone="faint">
                · {t(`zone.${observation.zone}`)} — {t('zoneDetail.notPhotographed')}
              </Text>
            ))}
          </Stack>
        ) : null}

        <WhyThis explanation={result.explanation} defaultOpen />

        <Button label={t('common.save')} onPress={onConfirm} />
      </Stack>
    </Card>
  );
}
