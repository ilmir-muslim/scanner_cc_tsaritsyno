import { createRouter, createWebHistory } from 'vue-router'
import ScannerView from '../views/ScannerView.vue'
import HistoryView from '../views/HistoryView.vue'
import PrintersView from '../views/PrintersView.vue'
import PhoneScannerView from '../views/PhoneScannerView.vue' 

const routes = [
    {
        path: '/',
        name: 'Scanner',
        component: ScannerView
    },
    {
        path: '/history',
        name: 'History',
        component: HistoryView
    },
    {
        path: '/printers',
        name: 'Printers',
        component: PrintersView
    },
    {
        path: '/phone-scanner',  
        name: 'PhoneScanner',
        component: PhoneScannerView
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router