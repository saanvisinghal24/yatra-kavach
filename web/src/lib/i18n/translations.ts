export type Language = 'en' | 'hi';

export interface Translations {
  appName: string;
  tagline: string;
  demoBadge: string;
  languageToggle: string;
  
  // Navigation & General
  navHome: string;
  navRegister: string;
  navVolunteer: string;
  navControl: string;
  back: string;
  submit: string;
  cancel: string;
  loading: string;
  online: string;
  offline: string;
  syncNow: string;
  pendingSync: string;

  // Registration
  regTitle: string;
  regSubtitle: string;
  stepRoute: string;
  stepLeader: string;
  stepMembers: string;
  selectYatra: string;
  selectRoute: string;
  leaderName: string;
  leaderPhone: string;
  emergencyName: string;
  emergencyPhone: string;
  groupSize: string;
  memberDetails: string;
  memberName: string;
  ageBand: string;
  healthNote: string;
  generatePass: string;
  itineraryWarning: string;

  // Pass View
  passTitle: string;
  passCode: string;
  presentAtCheckpoint: string;
  downloadPass: string;
  openTrailView: string;

  // Trail View
  trailTitle: string;
  elevationProfile: string;
  currentElevation: string;
  nextCheckpoint: string;
  estDuration: string;
  healthCheckin: string;
  sosEmergency: string;
  familyShare: string;
  scanCheckpoint: string;

  // Health / AMS
  healthTitle: string;
  healthSubtitle: string;
  headache: string;
  stomach: string;
  fatigue: string;
  dizziness: string;
  redFlagsTitle: string;
  confusion: string;
  ataxia: string;
  breathless: string;
  cough: string;
  evaluateScore: string;
  call112: string;
  call108: string;

  // SOS
  sosTitle: string;
  sosSubtitle: string;
  sosDialDisaster: string;
  sosDialMedical: string;
  sosSendSms: string;
  sosNotice: string;

  // Control Room
  controlTitle: string;
  activePilgrims: string;
  urgentAlerts: string;
  systemNormal: string;
  liveFeed: string;
  resolveAlert: string;
}

export const translations: Record<Language, Translations> = {
  en: {
    appName: "YATRA KAVACH",
    tagline: "HP Pilgrim Trail Safety System",
    demoBadge: "DEMO / SIMULATION MODE",
    languageToggle: "हिन्दी",

    navHome: "Home",
    navRegister: "Register Group",
    navVolunteer: "Volunteer Scanner",
    navControl: "Control Room",
    back: "Back",
    submit: "Submit",
    cancel: "Cancel",
    loading: "Loading...",
    online: "Online (Sync Active)",
    offline: "Offline Mode (Queued Locally)",
    syncNow: "Sync Offline Queue",
    pendingSync: "records awaiting sync",

    regTitle: "Group Yatra Registration",
    regSubtitle: "Offline-capable registration for high-altitude pilgrimage trails.",
    stepRoute: "1. Route & Schedule",
    stepLeader: "2. Group Leader & Emergency",
    stepMembers: "3. Member Vitals",
    selectYatra: "Select Pilgrimage Yatra",
    selectRoute: "Select Official Trail Route",
    leaderName: "Group Leader Full Name",
    leaderPhone: "Leader Mobile (10 digits)",
    emergencyName: "Emergency Contact Full Name",
    emergencyPhone: "Emergency Contact Mobile",
    groupSize: "Number of Pilgrims",
    memberDetails: "Group Members",
    memberName: "Member Name",
    ageBand: "Age Band",
    healthNote: "Medical notes / pre-existing conditions",
    generatePass: "Generate Offline Yatra Pass",
    itineraryWarning: "Acclimatization Warning (Rule R10): Sleeping elevation gain exceeds 500m/day above 3,000m.",

    passTitle: "Official Yatra Kavach Pass",
    passCode: "Group Pass Code",
    presentAtCheckpoint: "Present this QR pass to volunteers or scan checkpoint QR signs along the trail.",
    downloadPass: "Save Pass Offline",
    openTrailView: "Open Trail View & Map",

    trailTitle: "Pilgrim Trail Tracker",
    elevationProfile: "Survey Altitude & Checkpoints",
    currentElevation: "Current Altitude",
    nextCheckpoint: "Next Scheduled Checkpoint",
    estDuration: "Estimated Walking Time",
    healthCheckin: "AMS Health Self-Check",
    sosEmergency: "EMERGENCY SOS",
    familyShare: "Family Share Link",
    scanCheckpoint: "Scan Checkpoint QR",

    healthTitle: "Lake Louise AMS Self-Assessment",
    healthSubtitle: "Deterministic safety guidance. Not a medical diagnosis.",
    headache: "Headache Severity (0: None, 3: Severe/Incapacitating)",
    stomach: "Gastrointestinal (0: Normal, 3: Severe Nausea / Vomiting)",
    fatigue: "Fatigue / Weakness (0: None, 3: Incapacitating)",
    dizziness: "Dizziness / Lightheadedness (0: None, 3: Severe)",
    redFlagsTitle: "Critical Red Flags (Immediate Descent)",
    confusion: "Confusion, disorientation, or slurred speech",
    ataxia: "Loss of coordination / stumbling",
    breathless: "Severe breathlessness while resting",
    cough: "Persistent rattling cough / pink sputum",
    evaluateScore: "Evaluate Lake Louise Score",
    call112: "Call 112 (Disaster / Police)",
    call108: "Call 108 (Medical Ambulance)",

    sosTitle: "Emergency Distress Dispatch",
    sosSubtitle: "Works without cellular data. Direct calling & pre-filled SMS for ITBP / SDRF.",
    sosDialDisaster: "Call 112 (HP Disaster Management)",
    sosDialMedical: "Call 108 (State Emergency Medical)",
    sosSendSms: "Send Pre-filled Emergency SMS",
    sosNotice: "Stay calm. If mobile network is unavailable, send an able group member down to the nearest checkpoint post.",

    controlTitle: "Control Room Operations",
    activePilgrims: "Active Pilgrims on Trail",
    urgentAlerts: "Urgent Safety Alerts",
    systemNormal: "All Trails Nominal",
    liveFeed: "Live Stream Audit Log",
    resolveAlert: "Acknowledge / Resolve"
  },
  hi: {
    appName: "यात्रा कवच",
    tagline: "हिमाचल प्रदेश तीर्थ सुरक्षा प्रणाली",
    demoBadge: "डेमो / अनुकरण मोड",
    languageToggle: "English",

    navHome: "मुख्य पृष्ठ",
    navRegister: "दल पंजीकरण",
    navVolunteer: "स्वयंसेवक स्कैनर",
    navControl: "नियंत्रण कक्ष",
    back: "वापस",
    submit: "जमा करें",
    cancel: "रद्द करें",
    loading: "लोड हो रहा है...",
    online: "ऑनलाइन (सिंक सक्रिय)",
    offline: "ऑफ़लाइन मोड (स्थानीय रूप से सुरक्षित)",
    syncNow: "ऑफ़लाइन डेटा सिंक करें",
    pendingSync: "रिकॉर्ड सिंक होने बाकी हैं",

    regTitle: "तीर्थयात्री दल पंजीकरण",
    regSubtitle: "उच्च तुंगता तीर्थ यात्रा के लिए ऑफ़लाइन-सक्षम पंजीकरण प्रणाली।",
    stepRoute: "१. मार्ग एवं प्रस्थान समय",
    stepLeader: "२. दल प्रमुख व आपातकालीन संपर्क",
    stepMembers: "३. दल सदस्यों का विवरण",
    selectYatra: "तीर्थ यात्रा का चयन करें",
    selectRoute: "आधिकारिक मार्ग का चयन करें",
    leaderName: "दल प्रमुख का पूरा नाम",
    leaderPhone: "मोबाइल नंबर (१० अंक)",
    emergencyName: "आपातकालीन संपर्क का नाम",
    emergencyPhone: "आपातकालीन मोबाइल नंबर",
    groupSize: "यात्रियों की कुल संख्या",
    memberDetails: "दल के सदस्य",
    memberName: "सदस्य का नाम",
    ageBand: "आयु वर्ग",
    healthNote: "स्वास्थ्य विवरण / पूर्व बीमारी",
    generatePass: "ऑफ़लाइन यात्रा पास बनाएं",
    itineraryWarning: "अनुकूलन चेतावनी (नियम R10): ३,००० मीटर से ऊपर दैनिक ऊंचाई ५०० मीटर से अधिक बढ़ रही है।",

    passTitle: "आधिकारिक यात्रा कवच पास",
    passCode: "दल पास कोड",
    presentAtCheckpoint: "चेकपॉइंट पर स्वयंसेवकों को यह क्यूआर दिखाएं अथवा मार्ग के क्यूआर कोड स्कैन करें।",
    downloadPass: "पास ऑफ़लाइन सुरक्षित करें",
    openTrailView: "मार्ग व नक्शा देखें",

    trailTitle: "तीर्थ मार्ग ट्रैकर",
    elevationProfile: "सर्वेक्षण ऊंचाई एवं चेकपॉइंट्स",
    currentElevation: "वर्तमान ऊंचाई",
    nextCheckpoint: "अगला चेकपॉइंट",
    estDuration: "अनुमानित पैदल समय",
    healthCheckin: "ऊंचाई बीमारी (AMS) जांच",
    sosEmergency: "आपातकालीन एसओएस",
    familyShare: "पारिवारिक साझा लिंक",
    scanCheckpoint: "चेकपॉइंट क्यूआर स्कैन करें",

    healthTitle: "लेक लुईस एएमएस स्वास्थ्य स्व-मूल्यांकन",
    healthSubtitle: "सुरक्षा मार्गदर्शन मात्र, यह चिकित्सीय निदान नहीं है।",
    headache: "सिरदर्द की तीव्रता (०: कुछ नहीं, ३: अत्यधिक असहनीय)",
    stomach: "पेट / उल्टी की शिकायत (०: सामान्य, ३: अत्यधिक मतली/उल्टी)",
    fatigue: "थकान / कमजोरी (०: सामान्य, ३: चलने में असमर्थ)",
    dizziness: "चक्कर आना (०: नहीं, ३: अत्यधिक)",
    redFlagsTitle: "गंभीर खतरे के संकेत (तुरंत नीचे उतरें)",
    confusion: "भ्रम, असामान्य व्यवहार या अस्पष्ट बोली",
    ataxia: "संतुलन बिगड़ना / लड़खड़ा कर चलना",
    breathless: "विश्राम के समय भी अत्यधिक सांस फूलना",
    cough: "लगातार छाती में घरघराहट या गीली खांसी",
    evaluateScore: "स्कोर का मूल्यांकन करें",
    call112: "११२ पर कॉल करें (आपदा / पुलिस)",
    call108: "१०८ पर कॉल करें (चिकित्सा एम्बुलेंस)",

    sosTitle: "आपातकालीन संकट सहायता",
    sosSubtitle: "मोबाइल डेटा के बिना भी कार्य करता है। आईटीबीपी / एसडीआरएफ के लिए सीधा कॉल और एसएमएस।",
    sosDialDisaster: "११२ पर कॉल करें (हिमाचल आपदा प्रबंधन)",
    sosDialMedical: "१०८ पर कॉल करें (राज्य आपातकालीन चिकित्सा)",
    sosSendSms: "पहले से भरा आपातकालीन एसएमएस भेजें",
    sosNotice: "धैर्य रखें। यदि मोबाइल नेटवर्क उपलब्ध नहीं है, तो किसी स्वस्थ सदस्य को निकटतम चेकपॉइंट पोस्ट पर भेजें।",

    controlTitle: "नियंत्रण कक्ष प्रचालन",
    activePilgrims: "मार्ग पर सक्रिय तीर्थयात्री",
    urgentAlerts: "अति आवश्यक सुरक्षा अलर्ट",
    systemNormal: "सभी मार्ग सामान्य स्थिति में",
    liveFeed: "लाइव ऑडिट स्ट्रीम",
    resolveAlert: "सत्यापित / निस्तारित करें"
  }
};
