using System;
using System.Collections.Generic;

namespace PsychHospital.Hospital
{
    [Serializable]
    public class RoomTypeData
    {
        public string id;
        public string displayName;
        public string category;
        public int width;
        public int height;
        public int buildCost;
        public string colorHex;
    }

    /// JsonUtility cannot deserialize a bare top-level array, so room lists are wrapped.
    [Serializable]
    public class RoomTypeListWrapper
    {
        public List<RoomTypeData> rooms;
    }
}
