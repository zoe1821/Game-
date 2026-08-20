#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using PsychHospital.Core;

namespace PsychHospital.EditorTools
{
    /// One-time convenience: creates the Main scene with a single GameManager object.
    /// Everything else (camera, grid, UI, patients) is built by GameManager itself at
    /// runtime, so this script only needs real Unity Editor APIs -- no hand-authored
    /// scene YAML, which keeps the scene guaranteed-valid.
    public static class SceneSetup
    {
        private const string ScenePath = "Assets/Scenes/Main.unity";

        [MenuItem("Psychiatric Hospital Simulator/Setup V0.1 Scene")]
        public static void SetupScene()
        {
            if (!Directory.Exists("Assets/Scenes"))
            {
                Directory.CreateDirectory("Assets/Scenes");
            }

            UnityEngine.SceneManagement.Scene scene =
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var gameManagerGO = new GameObject("GameManager");
            gameManagerGO.AddComponent<GameManager>();

            EditorSceneManager.SaveScene(scene, ScenePath);

            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };

            Debug.Log("Psychiatric Hospital Simulator: escena V0.1 creada en " + ScenePath);
        }
    }
}
#endif
