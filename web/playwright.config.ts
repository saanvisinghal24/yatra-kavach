import {defineConfig} from '@playwright/test';
export default defineConfig({testDir:'./e2e',timeout:60000,use:{baseURL:process.env.PUBLIC_ORIGIN||'http://localhost:5173',headless:true,launchOptions:{executablePath:process.env.BROWSER_EXECUTABLE,args:['--no-sandbox','--disable-dev-shm-usage','--no-zygote','--use-gl=angle','--use-angle=swiftshader']}}});
