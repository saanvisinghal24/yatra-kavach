import {Link} from 'react-router-dom';
import {useTranslation} from '../lib/i18n/LanguageContext';
export function Landing(){const {language}=useTranslation();const hi=language==='hi';return <main className="page"><div className="contour-header"><p className="meta-label">Himachal Pradesh / हिमाचल प्रदेश</p><h1>{hi?'हर चौकी पर, साथ का भरोसा।':'Know the last checkpoint.'}</h1><p>{hi?'पहाड़ी तीर्थ यात्राओं के लिए ऑफलाइन चेक-इन और स्पष्ट सुरक्षा संकेत।':'Offline check-ins and explainable safety alerts for pilgrim trails.'}</p><Link className="btn btn-primary" to="/register">{hi?'यात्रा पंजीकरण':'Register your group'}</Link></div><section className="steps">{(hi?['दल का पंजीकरण करें। पास सुरक्षित रखें।','हर चौकी पर स्कैन करें। ऑफलाइन भी सहेजें।','नेटवर्क आने पर सिंक करें। सलाह देखें।']:['Register your group. Save your pass.','Scan each checkpoint. Save even offline.','Sync when connected. Read trail advice.']).map((s,i)=><article className="trail-card" key={s}><span className="numeral">0{i+1}</span><h2>{s}</h2></article>)}</section><h2>{hi?'यात्रा मार्ग':'Trails covered'}</h2><p>Manimahesh · Chamba / मणिमहेश · चंबा<br/>Kinner Kailash · Kinnaur / किन्नर कैलाश · किन्नौर<br/>Shrikhand Mahadev · Kullu / श्रीखंड महादेव · कुल्लू</p><p>{hi?'सांकेतिक डेटा। किन्नर कैलाश और श्रीखंड के मार्ग प्रारंभिक हैं। नैना देवी, चिंतपूर्णी और ज्वालाजी में भीड़ संचालन नियोजित है।':'Indicative data. Kinner Kailash and Shrikhand are skeleton trail seeds. Naina Devi, Chintpurni and Jwalaji crowd operations are planned.'}</p>
<section aria-labelledby="travel-heading" style={{marginBlock:'2rem'}}>
  <h2 id="travel-heading">{hi?'अपनी यात्रा की योजना बनाएँ':'Plan Your Travel'}</h2>
  <p>{hi?'यात्रा के विकल्प और उपलब्धता बुकिंग वेबसाइट पर देखें।':'Explore travel options and check availability on the booking provider’s website.'}</p>
  <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit, minmax(min(100%, 240px), 1fr))',gap:'1rem',marginBlock:'1rem'}}>
    <article className="trail-card">
      <h3>redBus</h3>
      <p>{hi?'अपनी यात्रा के लिए बस विकल्प खोजें।':'Search bus options for your journey.'}</p>
      <a className="btn btn-primary" href="https://www.redbus.in/" target="_blank" rel="noopener noreferrer" style={{marginTop:'1rem'}}>
        {hi?'redBus खोलें ↗':'Open redBus ↗'}
      </a>
    </article>
    <article className="trail-card">
      <h3>MakeMyTrip</h3>
      <p>{hi?'यात्रा और ठहरने के विकल्प देखें।':'Explore travel and accommodation options.'}</p>
      <a className="btn btn-primary" href="https://www.makemytrip.com/" target="_blank" rel="noopener noreferrer" style={{marginTop:'1rem'}}>
        {hi?'MakeMyTrip खोलें ↗':'Open MakeMyTrip ↗'}
      </a>
    </article>
  </div>
  <p><small>{hi?'लिंक नए टैब में खुलते हैं और इंटरनेट चाहिए। बुकिंग, भुगतान और रद्दीकरण संबंधित वेबसाइट संभालती है। ये बाहरी लिंक हैं, आधिकारिक साझेदारी नहीं।':'Links open in a new tab and require internet. The selected provider handles booking, payment and cancellations. These are external links, not an official partnership.'}</small></p>
</section>
<nav><Link className="btn" to="/volunteer">Volunteer mode / स्वयंसेवक</Link><Link className="btn" to="/control">Control-room login / नियंत्रण कक्ष</Link><Link className="btn" to="/about">Methodology / कार्यप्रणाली</Link></nav></main>;}
