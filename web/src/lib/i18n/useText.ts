import words from './screenText.json';
import {useTranslation} from './LanguageContext';
export function useText(){const {language}=useTranslation();return (text:string)=>language==='hi'?(words as Record<string,string>)[text]||text:text;}
