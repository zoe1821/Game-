using System;
using System.Collections.Generic;

namespace PsychHospital.Patients
{
    public enum PatientSex
    {
        Masculino,
        Femenino
    }

    /// V0.1 patient record: only the demographic basics from section 5 of the design
    /// document ("Informacion"). Clinical history, symptoms and internal psychological
    /// state arrive in later versions (V0.3+) and must not be faked here.
    [Serializable]
    public class PatientData
    {
        public int id;
        public string fullName;
        public int age;
        public PatientSex sex;
    }

    /// JsonUtility-friendly container for the name pools used to generate patients
    /// procedurally (design doc section 5: "generados proceduralmente").
    [Serializable]
    public class PatientNameData
    {
        public List<string> maleFirstNames;
        public List<string> femaleFirstNames;
        public List<string> lastNames;
    }
}
