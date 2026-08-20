using System;
using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;

namespace PsychHospital.Data
{
    /// Loads JSON files from StreamingAssets so game content is data-driven, not hardcoded.
    /// Works uniformly in the Editor, on desktop and on Android (where StreamingAssets
    /// lives inside a compressed APK and must be read through UnityWebRequest).
    public static class JsonDataService
    {
        public static IEnumerator LoadStreamingAsset<T>(string relativePath, Action<T> onLoaded)
        {
            string path = Path.Combine(Application.streamingAssetsPath, relativePath);
            string json;

            if (path.Contains("://"))
            {
                using (UnityWebRequest request = UnityWebRequest.Get(path))
                {
                    yield return request.SendWebRequest();
#if UNITY_2020_1_OR_NEWER
                    bool success = request.result == UnityWebRequest.Result.Success;
#else
                    bool success = !request.isNetworkError && !request.isHttpError;
#endif
                    if (!success)
                    {
                        Debug.LogError($"JsonDataService: failed to load '{relativePath}': {request.error}");
                        onLoaded(default);
                        yield break;
                    }
                    json = request.downloadHandler.text;
                }
            }
            else
            {
                if (!File.Exists(path))
                {
                    Debug.LogError($"JsonDataService: file not found '{path}'");
                    onLoaded(default);
                    yield break;
                }
                json = File.ReadAllText(path);
            }

            T data = JsonUtility.FromJson<T>(json);
            onLoaded(data);
        }
    }
}
