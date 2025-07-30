document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const statusEl = document.getElementById('status');
    const tokenInput = document.getElementById('token-input');
    const serverIdsInput = document.getElementById('server-ids');
    const addTokenBtn = document.getElementById('add-token-btn');
    const tokensContainer = document.getElementById('tokens-container');
    const scanIntervalInput = document.getElementById('scan-interval');
    const reactionDelayMinInput = document.getElementById('reaction-delay-min');
    const reactionDelayMaxInput = document.getElementById('reaction-delay-max');
    const autoStartInput = document.getElementById('auto-start');
    const saveSettingsBtn = document.getElementById('save-settings-btn');

    // تحميل التكوين عند بدء التشغيل
    loadConfig();

    // أحداث الأزرار
    startBtn.addEventListener('click', startBots);
    stopBtn.addEventListener('click', stopBots);
    addTokenBtn.addEventListener('click', addToken);
    saveSettingsBtn.addEventListener('click', saveSettings);

    // بدء البوتات
    async function startBots() {
        try {
            const response = await fetch('/api/start', {
                method: 'POST'
            });
            
            if (response.ok) {
                updateStatus('جاري التشغيل...');
                setTimeout(loadStatus, 2000);
            }
        } catch (error) {
            console.error('Error starting bots:', error);
            updateStatus('خطأ في بدء التشغيل');
        }
    }

    // إيقاف البوتات
    async function stopBots() {
        try {
            const response = await fetch('/api/stop', {
                method: 'POST'
            });
            
            if (response.ok) {
                updateStatus('تم الإيقاف');
                setTimeout(loadStatus, 2000);
            }
        } catch (error) {
            console.error('Error stopping bots:', error);
            updateStatus('خطأ في الإيقاف');
        }
    }

    // إضافة توكن جديد
    async function addToken() {
        const token = tokenInput.value.trim();
        const serverIds = serverIdsInput.value
            .split(',')
            .map(id => id.trim())
            .filter(id => id);
        
        if (!token) {
            alert('الرجاء إدخال توكن صحيح');
            return;
        }
        
        if (serverIds.length === 0) {
            alert('الرجاء إدخال معرف سيرفر واحد على الأقل');
            return;
        }
        
        try {
            const response = await fetch('/api/tokens', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    token,
                    guild_ids: serverIds
                })
            });
            
            if (response.ok) {
                tokenInput.value = '';
                serverIdsInput.value = '';
                loadTokens();
            } else {
                const error = await response.json();
                alert(`خطأ: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error adding token:', error);
            alert('حدث خطأ أثناء إضافة التوكن');
        }
    }

    // حذف توكن
    async function removeToken(token) {
        try {
            const response = await fetch(`/api/tokens/${encodeURIComponent(token)}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                loadTokens();
            } else {
                const error = await response.json();
                alert(`خطأ: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error removing token:', error);
            alert('حدث خطأ أثناء حذف التوكن');
        }
    }

    // حفظ الإعدادات
    async function saveSettings() {
        const settings = {
            scan_interval: parseInt(scanIntervalInput.value) || 15,
            reaction_delay: [
                parseFloat(reactionDelayMinInput.value) || 1.5,
                parseFloat(reactionDelayMaxInput.value) || 3.0
            ],
            auto_start: autoStartInput.checked
        };
        
        try {
            const response = await fetch('/api/settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            if (response.ok) {
                alert('تم حفظ الإعدادات بنجاح');
            } else {
                const error = await response.json();
                alert(`خطأ: ${error.detail}`);
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('حدث خطأ أثناء حفظ الإعدادات');
        }
    }

    // تحميل التكوين
    async function loadConfig() {
        try {
            // تحميل الإعدادات
            const settingsResponse = await fetch('/api/status');
            if (settingsResponse.ok) {
                const status = await settingsResponse.json();
                
                // تحديث واجهة الإعدادات
                scanIntervalInput.value = status.settings.scan_interval;
                reactionDelayMinInput.value = status.settings.reaction_delay[0];
                reactionDelayMaxInput.value = status.settings.reaction_delay[1];
                autoStartInput.checked = status.settings.auto_start;
                
                // تحديث الحالة
                updateStatus(status.running ? 'جاري التشغيل' : 'متوقف');
            }
            
            // تحميل التوكنات
            loadTokens();
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }

    // تحميل التوكنات
    async function loadTokens() {
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                const status = await response.json();
                tokensContainer.innerHTML = '';
                
                status.tokens.forEach(tokenData => {
                    const li = document.createElement('li');
                    
                    const tokenSpan = document.createElement('span');
                    tokenSpan.className = 'token';
                    tokenSpan.textContent = `${tokenData.token.substring(0, 10)}...`;
                    tokenSpan.title = tokenData.token;
                    
                    const serversSpan = document.createElement('span');
                    serversSpan.textContent = `السيرفرات: ${tokenData.guild_ids.join(', ')}`;
                    
                    const removeBtn = document.createElement('button');
                    removeBtn.className = 'remove-btn danger';
                    removeBtn.textContent = 'حذف';
                    removeBtn.onclick = () => removeToken(tokenData.token);
                    
                    li.appendChild(tokenSpan);
                    li.appendChild(serversSpan);
                    li.appendChild(removeBtn);
                    
                    tokensContainer.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Error loading tokens:', error);
        }
    }

    // تحميل حالة النظام
    async function loadStatus() {
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                const status = await response.json();
                updateStatus(status.running ? 'جاري التشغيل' : 'متوقف');
            }
        } catch (error) {
            console.error('Error loading status:', error);
            updateStatus('خطأ في جلب الحالة');
        }
    }

    // تحديث حالة النظام
    function updateStatus(text) {
        statusEl.textContent = `الحالة: ${text}`;
    }

    // تحميل التكوين الأولي
    loadConfig();
});
