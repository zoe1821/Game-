#if UNITY_EDITOR
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Tilemaps;
using UnityEngine.UI;
using RPG.Core;
using RPG.Inventory;
using RPG.NPC;
using RPG.Player;
using RPG.Powers;
using RPG.TimeSystem;
using RPG.UI;
using RPG.World;

namespace RPG.EditorTools
{
    /// <summary>
    /// Genera por codigo la escena jugable de la Fase 1 (MVP): mapa pequeno, jugador,
    /// 5 NPCs, objetos fisicos, dialogo, caja de accion libre, telequinesis y UI.
    /// Se construye por codigo (en vez de a mano en el editor) para que el resultado
    /// sea siempre reproducible y facil de revisar en el control de versiones.
    /// Uso: menu "RPG/Construir Escena MVP (Fase 1)".
    /// </summary>
    public static class MVPSceneBuilder
    {
        private const string GeneratedRoot = "Assets/_Project/Generated";
        private const string ScenePath = "Assets/_Project/Scenes/Phase1_MVP.unity";

        [MenuItem("RPG/Construir Escena MVP (Fase 1)")]
        public static void BuildScene()
        {
            EnsureFolders();

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            BuildGround();
            var camera = BuildCamera();

            var (playerGO, playerController, playerStats, playerInteractor, playerInventory, playerPowers) = BuildPlayer();
            camera.GetComponent<CameraFollow>().SetTarget(playerGO.transform);

            var telefonoItem = CreateItem("telefono", "Telefono", 0.3f, 200f);
            var libroItem = CreateItem("libro", "Libro", 0.6f, 15f);

            var npcs = BuildNPCs();
            BuildWorldObjects(telefonoItem, libroItem, npcs);

            var gameManagerGO = new GameObject("GameManager");
            var timeManager = gameManagerGO.AddComponent<TimeManager>();
            var gameManager = gameManagerGO.AddComponent<GameManager>();
            SetField(gameManager, "playerController", playerController);
            SetField(gameManager, "playerStats", playerStats);
            SetField(gameManager, "playerInteractor", playerInteractor);
            SetField(gameManager, "playerInventory", playerInventory);
            SetField(gameManager, "playerPowers", playerPowers);
            SetField(gameManager, "timeManager", timeManager);

            BuildUI(playerController, playerStats, timeManager, new[] { telefonoItem, libroItem });

            EditorUtility.SetDirty(gameManagerGO);
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene, ScenePath);

            Debug.Log($"[MVPSceneBuilder] Escena Fase 1 creada en {ScenePath}. Presiona Play para probarla.");
        }

        // ---------------------------------------------------------------- Mundo

        private static void BuildGround()
        {
            var gridGO = new GameObject("Grid", typeof(Grid));
            var tilemapGO = new GameObject("Ground", typeof(Tilemap), typeof(TilemapRenderer));
            tilemapGO.transform.SetParent(gridGO.transform);
            var tilemap = tilemapGO.GetComponent<Tilemap>();

            var groundSprite = CreateSquareSprite("ground_tile", new Color(0.36f, 0.62f, 0.36f));
            var tile = ScriptableObject.CreateInstance<Tile>();
            tile.sprite = groundSprite;
            string tilePath = $"{GeneratedRoot}/GroundTile.asset";
            AssetDatabase.DeleteAsset(tilePath);
            AssetDatabase.CreateAsset(tile, tilePath);

            for (int x = -12; x <= 12; x++)
                for (int y = -9; y <= 9; y++)
                    tilemap.SetTile(new Vector3Int(x, y, 0), tile);
        }

        private static GameObject BuildCamera()
        {
            var cameraGO = new GameObject("Main Camera", typeof(Camera), typeof(CameraFollow));
            cameraGO.tag = "MainCamera";
            var cam = cameraGO.GetComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 6f;
            cameraGO.transform.position = new Vector3(0, 0, -10);
            return cameraGO;
        }

        // ---------------------------------------------------------------- Jugador

        private static (GameObject, PlayerController, PlayerStats, PlayerInteractor, RPG.Inventory.InventorySystem, PowerController) BuildPlayer()
        {
            var go = new GameObject("Player", typeof(Rigidbody2D), typeof(BoxCollider2D), typeof(SpriteRenderer));
            go.transform.position = Vector3.zero;

            var sr = go.GetComponent<SpriteRenderer>();
            sr.sprite = CreateSquareSprite("player", new Color(0.2f, 0.5f, 0.95f));
            sr.sortingOrder = 5;

            var rb = go.GetComponent<Rigidbody2D>();
            rb.gravityScale = 0f;
            rb.freezeRotation = true;

            var controller = go.AddComponent<PlayerController>();
            var stats = go.AddComponent<PlayerStats>();
            var interactor = go.AddComponent<PlayerInteractor>();
            var inventory = go.AddComponent<RPG.Inventory.InventorySystem>();
            var powers = go.AddComponent<PowerController>();

            return (go, controller, stats, interactor, inventory, powers);
        }

        // ---------------------------------------------------------------- NPCs

        private static NPCController[] BuildNPCs()
        {
            var definitions = new[]
            {
                new NpcDefinition("emily", "Emily", 16, "Estudiante", new Vector3(-4, 3, 0), new Color(0.9f, 0.5f, 0.7f), 0.6f, 0.7f, 0.3f, 0.4f),
                new NpcDefinition("sarah", "Sarah", 16, "Estudiante", new Vector3(3, 3, 0), new Color(0.9f, 0.8f, 0.2f), 0.5f, 0.6f, 0.4f, 0.5f),
                new NpcDefinition("john", "John", 34, "Mecanico", new Vector3(-5, -3, 0), new Color(0.4f, 0.4f, 0.4f), 0.3f, 0.5f, 0.7f, 0.7f),
                new NpcDefinition("marcus", "Marcus", 45, "Profesor", new Vector3(5, -2, 0), new Color(0.3f, 0.3f, 0.7f), 0.5f, 0.8f, 0.4f, 0.3f),
                new NpcDefinition("lena", "Lena", 27, "Enfermera", new Vector3(0, -5, 0), new Color(0.8f, 0.3f, 0.3f), 0.8f, 0.7f, 0.5f, 0.3f),
            };

            var result = new NPCController[definitions.Length];
            for (int i = 0; i < definitions.Length; i++)
            {
                var def = definitions[i];

                var data = ScriptableObject.CreateInstance<NPCData>();
                data.npcId = def.Id;
                data.npcName = def.Name;
                data.age = def.Age;
                data.profession = def.Profession;
                data.startingMoney = 30f;
                data.portraitColor = def.Color;
                data.friendliness = def.Friendliness;
                data.honesty = def.Honesty;
                data.bravery = def.Bravery;
                data.temper = def.Temper;
                data.intelligence = 0.5f;
                data.interests = new[] { "musica", "videojuegos" };
                data.fears = new[] { "estar sola/o" };
                data.goals = new[] { "terminar sus estudios" };

                string assetPath = $"{GeneratedRoot}/NPCs/{def.Id}.asset";
                AssetDatabase.DeleteAsset(assetPath);
                AssetDatabase.CreateAsset(data, assetPath);

                var go = new GameObject($"NPC_{def.Name}", typeof(Rigidbody2D), typeof(BoxCollider2D), typeof(SpriteRenderer));
                go.transform.position = def.Position;

                var sr = go.GetComponent<SpriteRenderer>();
                sr.sprite = CreateSquareSprite($"npc_{def.Id}", def.Color);
                sr.sortingOrder = 5;

                var rb = go.GetComponent<Rigidbody2D>();
                rb.gravityScale = 0f;
                rb.drag = 6f;
                rb.angularDrag = 6f;
                rb.freezeRotation = true;

                var controller = go.AddComponent<NPCController>();
                SetField(controller, "data", data);

                result[i] = controller;
            }
            return result;
        }

        // ---------------------------------------------------------------- Objetos del mundo

        private static void BuildWorldObjects(ItemData telefonoItem, ItemData libroItem, NPCController[] npcs)
        {
            CreateWorldObject("silla", "Silla", new Vector3(-2, 1, 0), new Color(0.6f, 0.4f, 0.2f),
                weight: 4f, movable: true, destructible: false, pickable: false, usable: false);

            CreateWorldObject("mesa", "Mesa", new Vector3(1, 0, 0), new Color(0.5f, 0.3f, 0.15f),
                weight: 15f, movable: true, destructible: false, pickable: false, usable: false);

            CreateWorldObject("sillon", "Sillon", new Vector3(-1, -1, 0), new Color(0.4f, 0.2f, 0.5f),
                weight: 20f, movable: true, destructible: true, pickable: false, usable: false);

            CreateWorldObject("puerta", "Puerta", new Vector3(4, 1, 0), new Color(0.5f, 0.35f, 0.2f),
                weight: 30f, movable: false, destructible: false, pickable: false, usable: true);

            var pared = CreateWorldObject("pared", "Pared", new Vector3(6, 3, 0), new Color(0.55f, 0.55f, 0.55f),
                weight: 9999f, movable: false, destructible: false, pickable: false, usable: false, withRigidbody: false);
            pared.transform.localScale = new Vector3(1f, 3f, 1f);

            // El telefono le pertenece a Sarah: robarlo debe hacer que ella reaccione y lo recuerde.
            var telefonoObj = CreateWorldObject("telefono", "Telefono", new Vector3(3, 2, 0), new Color(0.1f, 0.1f, 0.1f),
                weight: 0.3f, movable: true, destructible: false, pickable: true, usable: true, item: telefonoItem);
            SetField(telefonoObj, "ownerId", "sarah");

            CreateWorldObject("libro", "Libro", new Vector3(-3, -2, 0), new Color(0.8f, 0.7f, 0.4f),
                weight: 0.6f, movable: true, destructible: false, pickable: true, usable: false, item: libroItem);
        }

        private static WorldObject CreateWorldObject(string id, string displayName, Vector3 position, Color color,
            float weight, bool movable, bool destructible, bool pickable, bool usable,
            ItemData item = null, bool withRigidbody = true)
        {
            var data = ScriptableObject.CreateInstance<WorldObjectData>();
            data.objectName = displayName;
            data.weight = weight;
            data.isMovable = movable;
            data.isDestructible = destructible;
            data.isPickable = pickable;
            data.isUsable = usable;
            data.correspondingItem = item;

            string assetPath = $"{GeneratedRoot}/WorldObjects/{id}.asset";
            AssetDatabase.DeleteAsset(assetPath);
            AssetDatabase.CreateAsset(data, assetPath);

            var components = withRigidbody
                ? new[] { typeof(BoxCollider2D), typeof(SpriteRenderer), typeof(Rigidbody2D) }
                : new[] { typeof(BoxCollider2D), typeof(SpriteRenderer) };

            var go = new GameObject(displayName, components);
            go.transform.position = position;

            var sr = go.GetComponent<SpriteRenderer>();
            sr.sprite = CreateSquareSprite($"obj_{id}", color);
            sr.sortingOrder = 3;

            if (withRigidbody)
            {
                var rb = go.GetComponent<Rigidbody2D>();
                rb.gravityScale = 0f;
                rb.drag = 2f;
                rb.angularDrag = 2f;
                rb.mass = Mathf.Max(0.1f, weight);
            }

            var worldObject = go.AddComponent<WorldObject>();
            SetField(worldObject, "objectId", id);
            SetField(worldObject, "data", data);

            return worldObject;
        }

        // ---------------------------------------------------------------- UI

        private enum Anchor { TopLeft, TopRight, BottomLeft, BottomRight, TopStretch, BottomStretch }

        private static void BuildUI(PlayerController playerController, PlayerStats playerStats,
            TimeManager timeManager, ItemData[] allItems)
        {
            new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));

            var canvasGO = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasGO.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGO.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1280, 720);

            Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var t = canvasGO.transform;

            // --- HUD superior ---
            var healthSlider = CreateSlider("HealthSlider", t, Anchor.TopLeft, new Vector2(10, -10), new Vector2(200, 18), new Color(0.8f, 0.2f, 0.2f));
            var energySlider = CreateSlider("EnergySlider", t, Anchor.TopLeft, new Vector2(10, -32), new Vector2(200, 18), new Color(0.2f, 0.5f, 0.9f));
            var moneyText = CreateText("MoneyText", t, "$0", 18, Anchor.TopLeft, new Vector2(10, -56), new Vector2(200, 24), TextAnchor.MiddleLeft, font);
            var powerText = CreateText("PowerText", t, "Poder Nv.1", 18, Anchor.TopLeft, new Vector2(10, -80), new Vector2(200, 24), TextAnchor.MiddleLeft, font);
            var timeText = CreateText("TimeText", t, "07:00", 18, Anchor.TopRight, new Vector2(-10, -10), new Vector2(160, 24), TextAnchor.MiddleRight, font);

            var hudGO = new GameObject("StatsHUD", typeof(RectTransform));
            hudGO.transform.SetParent(t, false);
            var hud = hudGO.AddComponent<StatsHUD>();
            SetField(hud, "playerStats", playerStats);
            SetField(hud, "timeManager", timeManager);
            SetField(hud, "healthSlider", healthSlider);
            SetField(hud, "energySlider", energySlider);
            SetField(hud, "moneyText", moneyText);
            SetField(hud, "powerLevelText", powerText);
            SetField(hud, "timeText", timeText);

            // --- Diario (journal) ---
            var journalText = CreateText("JournalText", t, "", 14, Anchor.BottomLeft, new Vector2(10, 100), new Vector2(420, 160), TextAnchor.LowerLeft, font);

            // --- Dialogo ---
            var dialoguePanel = CreatePanel("DialoguePanel", t, new Color(0, 0, 0, 0.75f), Anchor.TopRight, new Vector2(-10, -10), new Vector2(420, 140));
            var speakerText = CreateText("SpeakerText", dialoguePanel.transform, "NPC", 18, Anchor.TopLeft, new Vector2(10, -8), new Vector2(400, 24), TextAnchor.UpperLeft, font);
            var logText = CreateText("LogText", dialoguePanel.transform, "", 14, Anchor.TopLeft, new Vector2(10, -36), new Vector2(400, 96), TextAnchor.UpperLeft, font);

            var dialogueUIGO = new GameObject("DialogueUI", typeof(RectTransform));
            dialogueUIGO.transform.SetParent(t, false);
            var dialogueUI = dialogueUIGO.AddComponent<DialogueUI>();
            SetField(dialogueUI, "panelRoot", dialoguePanel);
            SetField(dialogueUI, "speakerNameText", speakerText);
            SetField(dialogueUI, "logText", logText);

            // --- Caja de accion libre (el centro del juego) ---
            var inputField = CreateInputField("ActionInputField", t, new Vector2(10, 10), new Vector2(-100, 44), font);
            var sendButton = CreateButton("SendButton", t, "Enviar", font, new Vector2(-10, 10), new Vector2(80, 44));
            var feedbackText = CreateText("FeedbackText", t, "Escribe cualquier accion libre...", 14, Anchor.BottomLeft, new Vector2(10, 58), new Vector2(600, 24), TextAnchor.LowerLeft, font);

            var actionInputGO = new GameObject("ActionInputUI", typeof(RectTransform));
            actionInputGO.transform.SetParent(t, false);
            var actionInputUI = actionInputGO.AddComponent<ActionInputUI>();
            SetField(actionInputUI, "inputField", inputField);
            SetField(actionInputUI, "sendButton", sendButton);
            SetField(actionInputUI, "feedbackText", feedbackText);
            SetField(actionInputUI, "playerController", playerController);

            var uiManagerGO = new GameObject("UIManager", typeof(RectTransform));
            uiManagerGO.transform.SetParent(t, false);
            var uiManager = uiManagerGO.AddComponent<UIManager>();
            SetField(uiManager, "journalText", journalText);
            SetField(uiManager, "allItemsForLoad", allItems);
        }

        // ---------------------------------------------------------------- Helpers de UI

        private static void ApplyAnchor(RectTransform rt, Anchor anchor, Vector2 anchoredPos, Vector2 size)
        {
            switch (anchor)
            {
                case Anchor.TopLeft:
                    rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
                    rt.pivot = new Vector2(0, 1);
                    rt.anchoredPosition = anchoredPos;
                    rt.sizeDelta = size;
                    break;
                case Anchor.TopRight:
                    rt.anchorMin = rt.anchorMax = new Vector2(1, 1);
                    rt.pivot = new Vector2(1, 1);
                    rt.anchoredPosition = anchoredPos;
                    rt.sizeDelta = size;
                    break;
                case Anchor.BottomLeft:
                    rt.anchorMin = rt.anchorMax = new Vector2(0, 0);
                    rt.pivot = new Vector2(0, 0);
                    rt.anchoredPosition = anchoredPos;
                    rt.sizeDelta = size;
                    break;
                case Anchor.BottomRight:
                    rt.anchorMin = rt.anchorMax = new Vector2(1, 0);
                    rt.pivot = new Vector2(1, 0);
                    rt.anchoredPosition = anchoredPos;
                    rt.sizeDelta = size;
                    break;
                case Anchor.TopStretch:
                    rt.anchorMin = new Vector2(0, 1);
                    rt.anchorMax = new Vector2(1, 1);
                    rt.pivot = new Vector2(0.5f, 1);
                    rt.offsetMin = new Vector2(anchoredPos.x, anchoredPos.y - size.y);
                    rt.offsetMax = new Vector2(-anchoredPos.x, anchoredPos.y);
                    break;
                case Anchor.BottomStretch:
                    rt.anchorMin = new Vector2(0, 0);
                    rt.anchorMax = new Vector2(1, 0);
                    rt.pivot = new Vector2(0.5f, 0);
                    rt.offsetMin = new Vector2(anchoredPos.x, anchoredPos.y);
                    rt.offsetMax = new Vector2(-anchoredPos.x, anchoredPos.y + size.y);
                    break;
            }
        }

        private static Text CreateText(string name, Transform parent, string content, int fontSize,
            Anchor anchor, Vector2 anchoredPos, Vector2 size, TextAnchor alignment, Font font)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Text));
            go.transform.SetParent(parent, false);
            ApplyAnchor(go.GetComponent<RectTransform>(), anchor, anchoredPos, size);

            var text = go.GetComponent<Text>();
            text.text = content;
            text.font = font;
            text.fontSize = fontSize;
            text.alignment = alignment;
            text.color = Color.white;
            text.horizontalOverflow = HorizontalWrapMode.Wrap;
            text.verticalOverflow = VerticalWrapMode.Overflow;
            return text;
        }

        private static GameObject CreatePanel(string name, Transform parent, Color color, Anchor anchor, Vector2 anchoredPos, Vector2 size)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            ApplyAnchor(go.GetComponent<RectTransform>(), anchor, anchoredPos, size);
            go.GetComponent<Image>().color = color;
            return go;
        }

        private static Slider CreateSlider(string name, Transform parent, Anchor anchor, Vector2 anchoredPos, Vector2 size, Color fillColor)
        {
            var root = new GameObject(name, typeof(RectTransform), typeof(Slider));
            root.transform.SetParent(parent, false);
            ApplyAnchor(root.GetComponent<RectTransform>(), anchor, anchoredPos, size);

            var bgGO = new GameObject("Background", typeof(RectTransform), typeof(Image));
            bgGO.transform.SetParent(root.transform, false);
            var bgRT = bgGO.GetComponent<RectTransform>();
            bgRT.anchorMin = Vector2.zero; bgRT.anchorMax = Vector2.one; bgRT.offsetMin = Vector2.zero; bgRT.offsetMax = Vector2.zero;
            bgGO.GetComponent<Image>().color = new Color(0.15f, 0.15f, 0.15f, 0.9f);

            var fillAreaGO = new GameObject("Fill Area", typeof(RectTransform));
            fillAreaGO.transform.SetParent(root.transform, false);
            var fillAreaRT = fillAreaGO.GetComponent<RectTransform>();
            fillAreaRT.anchorMin = Vector2.zero; fillAreaRT.anchorMax = Vector2.one; fillAreaRT.offsetMin = Vector2.zero; fillAreaRT.offsetMax = Vector2.zero;

            var fillGO = new GameObject("Fill", typeof(RectTransform), typeof(Image));
            fillGO.transform.SetParent(fillAreaGO.transform, false);
            var fillRT = fillGO.GetComponent<RectTransform>();
            fillRT.anchorMin = Vector2.zero; fillRT.anchorMax = Vector2.one; fillRT.offsetMin = Vector2.zero; fillRT.offsetMax = Vector2.zero;
            fillGO.GetComponent<Image>().color = fillColor;

            var slider = root.GetComponent<Slider>();
            slider.fillRect = fillRT;
            slider.targetGraphic = fillGO.GetComponent<Image>();
            slider.interactable = false;
            slider.minValue = 0; slider.maxValue = 100; slider.value = 100;
            return slider;
        }

        private static Button CreateButton(string name, Transform parent, string label, Font font, Vector2 anchoredPos, Vector2 size)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image), typeof(Button));
            go.transform.SetParent(parent, false);
            ApplyAnchor(go.GetComponent<RectTransform>(), Anchor.BottomRight, anchoredPos, size);
            go.GetComponent<Image>().color = new Color(0.2f, 0.6f, 0.3f);

            var textGO = new GameObject("Text", typeof(RectTransform), typeof(Text));
            textGO.transform.SetParent(go.transform, false);
            var textRT = textGO.GetComponent<RectTransform>();
            textRT.anchorMin = Vector2.zero; textRT.anchorMax = Vector2.one; textRT.offsetMin = Vector2.zero; textRT.offsetMax = Vector2.zero;
            var text = textGO.GetComponent<Text>();
            text.text = label;
            text.font = font;
            text.alignment = TextAnchor.MiddleCenter;
            text.color = Color.white;

            return go.GetComponent<Button>();
        }

        /// <summary>Caja de texto libre, anclada abajo y estirada horizontalmente (deja hueco a la derecha para el boton).</summary>
        private static InputField CreateInputField(string name, Transform parent, Vector2 bottomLeftOffset, Vector2 rightMarginAndHeight, Font font)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image), typeof(InputField));
            go.transform.SetParent(parent, false);
            var rt = go.GetComponent<RectTransform>();
            rt.anchorMin = new Vector2(0, 0);
            rt.anchorMax = new Vector2(1, 0);
            rt.pivot = new Vector2(0, 0);
            rt.offsetMin = new Vector2(bottomLeftOffset.x, bottomLeftOffset.y);
            rt.offsetMax = new Vector2(rightMarginAndHeight.x, bottomLeftOffset.y + rightMarginAndHeight.y);
            go.GetComponent<Image>().color = new Color(1f, 1f, 1f, 0.9f);

            var textGO = new GameObject("Text", typeof(RectTransform), typeof(Text));
            textGO.transform.SetParent(go.transform, false);
            var textRT = textGO.GetComponent<RectTransform>();
            textRT.anchorMin = Vector2.zero; textRT.anchorMax = Vector2.one;
            textRT.offsetMin = new Vector2(8, 4); textRT.offsetMax = new Vector2(-8, -4);
            var text = textGO.GetComponent<Text>();
            text.font = font;
            text.color = Color.black;
            text.alignment = TextAnchor.MiddleLeft;
            text.supportRichText = false;

            var placeholderGO = new GameObject("Placeholder", typeof(RectTransform), typeof(Text));
            placeholderGO.transform.SetParent(go.transform, false);
            var placeholderRT = placeholderGO.GetComponent<RectTransform>();
            placeholderRT.anchorMin = Vector2.zero; placeholderRT.anchorMax = Vector2.one;
            placeholderRT.offsetMin = new Vector2(8, 4); placeholderRT.offsetMax = new Vector2(-8, -4);
            var placeholder = placeholderGO.GetComponent<Text>();
            placeholder.font = font;
            placeholder.text = "Escribe una accion libre (ej: 'uso telequinesis para levantar la silla')...";
            placeholder.color = new Color(0, 0, 0, 0.5f);
            placeholder.fontStyle = FontStyle.Italic;

            var inputField = go.GetComponent<InputField>();
            inputField.textComponent = text;
            inputField.placeholder = placeholder;
            inputField.lineType = InputField.LineType.SingleLine;

            return inputField;
        }

        // ---------------------------------------------------------------- Utilidades generales

        private static Sprite CreateSquareSprite(string name, Color color, int size = 8, int pixelsPerUnit = 8)
        {
            string path = $"{GeneratedRoot}/Sprites/{name}.png";
            if (!AssetDatabase.IsValidFolder($"{GeneratedRoot}/Sprites"))
                AssetDatabase.CreateFolder(GeneratedRoot, "Sprites");

            var texture = new Texture2D(size, size, TextureFormat.RGBA32, false);
            var pixels = new Color[size * size];
            for (int i = 0; i < pixels.Length; i++) pixels[i] = color;
            texture.SetPixels(pixels);
            texture.Apply();

            File.WriteAllBytes(path, texture.EncodeToPNG());
            Object.DestroyImmediate(texture);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);

            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = pixelsPerUnit;
            importer.filterMode = FilterMode.Point;
            importer.mipmapEnabled = false;
            EditorUtility.SetDirty(importer);
            importer.SaveAndReimport();

            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }

        private static ItemData CreateItem(string id, string name, float weight, float value)
        {
            string path = $"{GeneratedRoot}/Items/{id}.asset";
            var item = ScriptableObject.CreateInstance<ItemData>();
            item.itemId = id;
            item.itemName = name;
            item.weight = weight;
            item.value = value;

            AssetDatabase.DeleteAsset(path);
            AssetDatabase.CreateAsset(item, path);
            return item;
        }

        private static void EnsureFolders()
        {
            CreateFolderRecursive("Assets/_Project/Scenes");
            CreateFolderRecursive(GeneratedRoot);
            CreateFolderRecursive($"{GeneratedRoot}/NPCs");
            CreateFolderRecursive($"{GeneratedRoot}/WorldObjects");
            CreateFolderRecursive($"{GeneratedRoot}/Items");
            CreateFolderRecursive($"{GeneratedRoot}/Sprites");
        }

        private static void CreateFolderRecursive(string path)
        {
            if (AssetDatabase.IsValidFolder(path)) return;
            string parent = Path.GetDirectoryName(path).Replace('\\', '/');
            string folderName = Path.GetFileName(path);
            if (!AssetDatabase.IsValidFolder(parent)) CreateFolderRecursive(parent);
            AssetDatabase.CreateFolder(parent, folderName);
        }

        /// <summary>Asigna un campo privado (SerializeField) de un componente generado por codigo.</summary>
        private static void SetField(object target, string fieldName, object value)
        {
            var field = target.GetType().GetField(fieldName, BindingFlags.NonPublic | BindingFlags.Public | BindingFlags.Instance);
            if (field == null)
            {
                Debug.LogError($"[MVPSceneBuilder] No se encontro el campo '{fieldName}' en {target.GetType().Name}.");
                return;
            }
            field.SetValue(target, value);
            if (target is Object unityObject) EditorUtility.SetDirty(unityObject);
        }

        private readonly struct NpcDefinition
        {
            public readonly string Id;
            public readonly string Name;
            public readonly int Age;
            public readonly string Profession;
            public readonly Vector3 Position;
            public readonly Color Color;
            public readonly float Friendliness;
            public readonly float Honesty;
            public readonly float Bravery;
            public readonly float Temper;

            public NpcDefinition(string id, string name, int age, string profession, Vector3 position, Color color,
                float friendliness, float honesty, float bravery, float temper)
            {
                Id = id; Name = name; Age = age; Profession = profession; Position = position; Color = color;
                Friendliness = friendliness; Honesty = honesty; Bravery = bravery; Temper = temper;
            }
        }
    }
}
#endif
