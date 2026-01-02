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

// 注册
window.register = async function register(username, password, managerUsername, email, phone) {
    try {
        const requestData = {
            username,
            password,
            manager_username: managerUsername
        };
        if (email) requestData.email = email;
        if (phone) requestData.phone = phone;
        
        const response = await window.apiRequest('/users/register', {
            method: 'POST',
            body: JSON.stringify(requestData),
        });
        return response;
    } catch (error) {
        throw error;
    }
}

// 选项卡切换
document.addEventListener('DOMContentLoaded', () => {
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginFormContainer = document.getElementById('loginFormContainer');
    const registerFormContainer = document.getElementById('registerFormContainer');
    
    if (loginTab && registerTab) {
        loginTab.addEventListener('click', () => {
            loginTab.classList.add('active');
            loginTab.style.borderBottom = '3px solid #4472C4';
            registerTab.classList.remove('active');
            registerTab.style.borderBottom = 'none';
            loginFormContainer.style.display = 'block';
            registerFormContainer.style.display = 'none';
        });
        
        registerTab.addEventListener('click', () => {
            registerTab.classList.add('active');
            registerTab.style.borderBottom = '3px solid #4472C4';
            loginTab.classList.remove('active');
            loginTab.style.borderBottom = 'none';
            loginFormContainer.style.display = 'none';
            registerFormContainer.style.display = 'block';
        });
    }
});

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

// 注册页面初始化
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('registerUsername').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('registerConfirmPassword').value;
        const email = document.getElementById('registerEmail').value.trim();
        const phone = document.getElementById('registerPhone').value.trim();
        const managerUsername = document.getElementById('managerUsername').value;
        const errorMessage = document.getElementById('errorMessage');
        
        // 验证密码
        if (password !== confirmPassword) {
            errorMessage.textContent = '两次输入的密码不一致';
            errorMessage.classList.remove('hidden');
            return;
        }
        
        if (!password || password.length < 1) {
            errorMessage.textContent = '密码不能为空';
            errorMessage.classList.remove('hidden');
            return;
        }
        
        try {
            const result = await register(username, password, managerUsername, email || null, phone || null);
            if (result.success) {
                errorMessage.textContent = '注册成功，正在跳转...';
                errorMessage.classList.remove('hidden');
                errorMessage.classList.remove('error');
                errorMessage.classList.add('success');
                setTimeout(() => {
                    window.location.href = '/main';
                }, 1000);
            } else {
                errorMessage.textContent = result.message || '注册失败';
                errorMessage.classList.remove('hidden');
                errorMessage.classList.remove('success');
                errorMessage.classList.add('error');
            }
        } catch (error) {
            errorMessage.textContent = error.message || '注册失败，请检查网络连接';
            errorMessage.classList.remove('hidden');
            errorMessage.classList.remove('success');
            errorMessage.classList.add('error');
        }
    });
}

