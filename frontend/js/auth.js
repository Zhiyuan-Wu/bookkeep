/**
 * 认证相关功能
 */

// 检查登录状态
window.checkAuth = async function checkAuth() {
    try {
        const response = await window.apiRequest('/users/me');
        return response;
    } catch (error) {
        return null;
    }
}

// 登录
window.login = async function login(username, password) {
    try {
        const response = await window.apiRequest('/users/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        return response;
    } catch (error) {
        throw error;
    }
}

// 登出
window.logout = async function logout() {
    try {
        await window.apiRequest('/users/logout', {
            method: 'POST',
        });
        window.location.href = '/';
    } catch (error) {
        console.error('登出失败:', error);
    }
}

// 登录页面初始化
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const errorMessage = document.getElementById('errorMessage');
        
        try {
            const result = await login(username, password);
            if (result.success) {
                window.location.href = '/main';
            } else {
                errorMessage.textContent = result.message || '登录失败';
                errorMessage.classList.remove('hidden');
                // 确保错误消息显示在右上角（CSS已定义，这里确保样式正确）
                if (!errorMessage.style.position) {
                    errorMessage.style.position = 'fixed';
                    errorMessage.style.top = '20px';
                    errorMessage.style.right = '20px';
                    errorMessage.style.zIndex = '1001';
                }
            }
        } catch (error) {
            errorMessage.textContent = error.message || '登录失败，请检查网络连接';
            errorMessage.classList.remove('hidden');
            // 确保错误消息显示在右上角
            if (!errorMessage.style.position) {
                errorMessage.style.position = 'fixed';
                errorMessage.style.top = '20px';
                errorMessage.style.right = '20px';
                errorMessage.style.zIndex = '1001';
            }
        }
    });
}

