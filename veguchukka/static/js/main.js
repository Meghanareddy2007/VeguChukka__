// Veguchukka Main JS

// Set current date in Telugu
const teluguMonths = ['జనవరి','ఫిబ్రవరి','మార్చి','ఏప్రిల్','మే','జూన్','జూలై','ఆగస్టు','సెప్టెంబర్','అక్టోబర్','నవంబర్','డిసెంబర్'];
const teluguDays = ['ఆదివారం','సోమవారం','మంగళవారం','బుధవారం','గురువారం','శుక్రవారం','శనివారం'];
const now = new Date();
const dateStr = `${teluguDays[now.getDay()]}, ${now.getDate()} ${teluguMonths[now.getMonth()]} ${now.getFullYear()}`;
const el = document.getElementById('currentDate');
if (el) el.textContent = dateStr;

// Auto-dismiss alerts
setTimeout(() => {
    document.querySelectorAll('.alert').forEach(a => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(a);
        if (bsAlert) bsAlert.close();
    });
}, 4000);
