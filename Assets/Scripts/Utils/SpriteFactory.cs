using UnityEngine;

namespace PsychHospital.Utils
{
    /// Generates simple runtime sprites (solid room footprints, patient markers, floor tiling)
    /// so V0.1 has no dependency on imported art assets yet.
    public static class SpriteFactory
    {
        public static Sprite CreateSolidSprite(int cellsWide, int cellsTall, Color fill, int pixelsPerCell = 32)
        {
            int w = Mathf.Max(1, cellsWide) * pixelsPerCell;
            int h = Mathf.Max(1, cellsTall) * pixelsPerCell;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
            var border = fill * 0.7f;
            border.a = 1f;
            var pixels = new Color[w * h];
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    bool edge = x == 0 || y == 0 || x == w - 1 || y == h - 1;
                    pixels[y * w + x] = edge ? border : fill;
                }
            }
            tex.SetPixels(pixels);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), pixelsPerCell);
        }

        public static Sprite CreateCircleSprite(Color fill, int diameterPixels = 24)
        {
            int d = diameterPixels;
            var tex = new Texture2D(d, d, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear };
            var pixels = new Color[d * d];
            float radius = d / 2f;
            var center = new Vector2(radius, radius);
            for (int y = 0; y < d; y++)
            {
                for (int x = 0; x < d; x++)
                {
                    float dist = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), center);
                    pixels[y * d + x] = dist <= radius ? fill : Color.clear;
                }
            }
            tex.SetPixels(pixels);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, d, d), new Vector2(0.5f, 0.5f), diameterPixels);
        }

        public static Sprite CreateFloorSprite(int cellsWide, int cellsTall, int pixelsPerCell = 32)
        {
            int w = cellsWide * pixelsPerCell;
            int h = cellsTall * pixelsPerCell;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point };
            var a = new Color(0.85f, 0.85f, 0.87f);
            var b = new Color(0.80f, 0.80f, 0.82f);
            var pixels = new Color[w * h];
            for (int y = 0; y < h; y++)
            {
                for (int x = 0; x < w; x++)
                {
                    int cellX = x / pixelsPerCell;
                    int cellY = y / pixelsPerCell;
                    bool gridLine = (x % pixelsPerCell == 0) || (y % pixelsPerCell == 0);
                    Color baseColor = ((cellX + cellY) % 2 == 0) ? a : b;
                    pixels[y * w + x] = gridLine ? baseColor * 0.9f : baseColor;
                }
            }
            tex.SetPixels(pixels);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0f, 0f), pixelsPerCell);
        }
    }
}
