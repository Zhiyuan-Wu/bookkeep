/**
 * 系统设置功能
 */

// 初始化设置页面
document.addEventListener('DOMContentLoaded', () => {
    const changePasswordForm = document.getElementById('changePasswordForm');
    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            await changePassword();
        });
    }
});

// 修改密码
async function changePassword() {
    const form = document.getElementById('changePasswordForm');
    const data = getFormData(form);
    
    // 验证密码是否一致
    if (data.password !== data.confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    // 验证密码长度
    if (!data.password || data.password.length < 1) {
        showMessage('密码不能为空', 'error');
        return;
    }
    
    try {
        await apiRequest('/users/me/password', {
            method: 'PUT',
            body: JSON.stringify({ password: data.password })
        });
        showMessage('密码修改成功', 'success');
        form.reset();
    } catch (error) {
        showMessage('密码修改失败: ' + error.message, 'error');
    }
}

// 加载用户列表（管理员）
async function loadUsers() {
    try {
        const users = await apiRequest('/users/');
        renderUsersTable(users);
    } catch (error) {
        showMessage('加载用户列表失败: ' + error.message, 'error');
    }
}

// 渲染用户表格
function renderUsersTable(users) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = '';
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }
    
    users.forEach(user => {
        const row = document.createElement('tr');
        
        const actions = `
            <div class="action-buttons">
                <button class="action-btn" onclick="editUserPassword(${user.id})" title="修改密码">
                    <i class="fas fa-key"></i>
                </button>
                <button class="action-btn" onclick="editUserContact(${user.id})" title="修改联系方式">
                    <i class="fas fa-address-book"></i>
                </button>
                <button class="action-btn btn-danger" onclick="deleteUser(${user.id})" title="删除用户">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        
        const contactInfo = [];
        if (user.email) contactInfo.push(`📧 ${user.email}`);
        if (user.phone) contactInfo.push(`📱 ${user.phone}`);
        const contactHtml = contactInfo.length > 0 ? `<br><small style="color: #666;">${contactInfo.join(' ')}</small>` : '';
        
        row.innerHTML = `
            <td>${actions}</td>
            <td>${user.id}</td>
            <td>${user.username}${contactHtml}</td>
            <td>${user.user_type}</td>
            <td>${formatDate(user.created_at)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// 编辑用户密码
async function editUserPassword(userId) {
    const newPassword = prompt('请输入新密码:');
    if (!newPassword) return;
    
    try {
        await apiRequest(`/users/${userId}/password`, {
            method: 'PUT',
            body: JSON.stringify({ password: newPassword })
        });
        showMessage('密码修改成功', 'success');
    } catch (error) {
        showMessage('密码修改失败: ' + error.message, 'error');
    }
}

// 编辑用户联系方式
async function editUserContact(userId) {
    // 获取用户信息
    const users = await apiRequest('/users/');
    const user = users.find(u => u.id === userId);
    if (!user) {
        showMessage('用户不存在', 'error');
        return;
    }
    
    const formHtml = `
        <form id="contactForm">
            <div class="form-group">
                <label>
                    <i class="fas fa-envelope"></i>
                    邮箱
                </label>
                <input type="email" name="email" value="${user.email || ''}" placeholder="请输入邮箱地址">
            </div>
            <div class="form-group">
                <label>
                    <i class="fas fa-phone"></i>
                    手机号
                </label>
                <input type="text" name="phone" value="${user.phone || ''}" placeholder="请输入手机号">
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal('contactModal')">取消</button>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save"></i> 保存
                </button>
            </div>
        </form>
    `;
    
    const modal = createModal('contactModal', '修改联系方式', formHtml);
    document.getElementById('modalContainer').appendChild(modal);
    openModal('contactModal');
    
    // 绑定表单提交事件
    document.getElementById('contactForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const form = document.getElementById('contactForm');
        const formData = getFormData(form);
        
        try {
            await apiRequest(`/users/${userId}/contact`, {
                method: 'PUT',
                body: JSON.stringify({
                    email: formData.email || null,
                    phone: formData.phone || null
                })
            });
            showMessage('联系方式修改成功', 'success');
            closeModal('contactModal');
            loadUsers();
        } catch (error) {
            showMessage('联系方式修改失败: ' + error.message, 'error');
        }
    });
}

// 删除用户
async function deleteUser(userId) {
    if (!await confirmDialog('确定要删除这个用户吗？删除用户将同时删除所有关联商品。')) {
        return;
    }
    
    try {
        await apiRequest(`/users/${userId}`, { method: 'DELETE' });
        showMessage('用户删除成功', 'success');
        loadUsers();
    } catch (error) {
        showMessage('删除用户失败: ' + error.message, 'error');
    }
}

// 打开新建用户模态框
function openUserModal() {
    const formHtml = `
        <form id="userForm">
            <div class="form-group">
                <label>
                    <i class="fas fa-user"></i>
                    用户名 *
                </label>
                <input type="text" name="username" required maxlength="50" placeholder="请输入用户名">
            </div>
            <div class="form-group">
                <label>
                    <i class="fas fa-lock"></i>
                    密码 *
                </label>
                <input type="text" name="password" required autocomplete="new-password" class="password-input" placeholder="请输入密码">
            </div>
            <div class="form-group">
                <label>
                    <i class="fas fa-lock"></i>
                    确认密码 *
                </label>
                <input type="text" name="confirmPassword" required autocomplete="new-password" class="password-input" placeholder="请再次输入密码">
            </div>
            <div class="form-group">
                <label>
                    <i class="fas fa-user-tag"></i>
                    用户类型 *
                </label>
                <div class="visibility-selector">
                    <div class="radio-item">
                        <input type="radio" name="user_type" value="管理员" id="userTypeAdmin" required>
                        <span><i class="fas fa-user-shield"></i> 管理员</span>
                    </div>
                    <div class="radio-item">
                        <input type="radio" name="user_type" value="普通用户" id="userTypeNormal" required>
                        <span><i class="fas fa-user"></i> 普通用户</span>
                    </div>
                    <div class="radio-item">
                        <input type="radio" name="user_type" value="厂家" id="userTypeSupplier" required>
                        <span><i class="fas fa-building"></i> 厂家</span>
                    </div>
                    <div class="radio-item">
                        <input type="radio" name="user_type" value="学生用户" id="userTypeStudent" required>
                        <span><i class="fas fa-user-graduate"></i> 学生用户</span>
                    </div>
                </div>
            </div>
            <div class="form-group" id="managerUserGroup" style="display: none;">
                <label>
                    <i class="fas fa-user-tie"></i>
                    管理用户 *
                </label>
                <select name="manager_id" id="managerSelect" required>
                    <option value="">请选择管理用户</option>
                </select>
                <small style="color: #666; font-size: 12px;">学生用户必须指定一个普通用户作为管理用户</small>
            </div>
            <div class="form-group">
                <label>
                    <i class="fas fa-envelope"></i>
                    邮箱（可选）
                </label>
                <input type="email" name="email" placeholder="请输入邮箱地址">
            </div>
            <div class="form-group">
                <label>
                    <i class="fas fa-phone"></i>
                    手机号（可选）
                </label>
                <input type="text" name="phone" placeholder="请输入手机号">
            </div>
            <div class="form-actions">
                <button type="button" class="btn btn-secondary" onclick="closeModal('userModal')">取消</button>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-save"></i> 保存
                </button>
            </div>
        </form>
    `;
    
    const modal = createModal('userModal', '新建用户', formHtml);
    document.getElementById('modalContainer').appendChild(modal);
    openModal('userModal');
    
    // 加载普通用户列表（用于学生用户的管理用户选择）
    loadNormalUsersForManager();
    
    // 绑定单选按钮点击事件，确保选中状态正确显示
    const radioItems = modal.querySelectorAll('.radio-item');
    const managerUserGroup = modal.querySelector('#managerUserGroup');
    const managerSelect = modal.querySelector('#managerSelect');
    
    radioItems.forEach(item => {
        const radio = item.querySelector('input[type="radio"]');
        if (radio) {
            // 点击整个radio-item时，选中对应的radio
            item.addEventListener('click', (e) => {
                if (e.target !== radio) {
                    radio.checked = true;
                    // 触发change事件，确保样式更新
                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
            
            // 监听radio的change事件，更新样式和管理用户选择框显示
            radio.addEventListener('change', () => {
                // 移除所有选中状态
                radioItems.forEach(ri => {
                    ri.classList.remove('selected');
                });
                // 添加当前选中状态
                if (radio.checked) {
                    item.classList.add('selected');
                }
                
                // 如果是学生用户，显示管理用户选择框
                if (radio.value === '学生用户') {
                    managerUserGroup.style.display = 'block';
                    managerSelect.required = true;
                } else {
                    managerUserGroup.style.display = 'none';
                    managerSelect.required = false;
                    managerSelect.value = '';
                }
            });
        }
    });
    
    // 绑定表单提交事件
    document.getElementById('userForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createUserFromForm();
    });
}

// 从表单创建用户
async function createUserFromForm() {
    const form = document.getElementById('userForm');
    const formData = getFormData(form);
    
    // 验证密码是否一致
    if (formData.password !== formData.confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }
    
    // 验证密码长度
    if (!formData.password || formData.password.length < 1) {
        showMessage('密码不能为空', 'error');
        return;
    }
    
    // 验证用户类型
    if (!formData.user_type) {
        showMessage('请选择用户类型', 'error');
        return;
    }
    
    try {
        const requestData = {
            username: formData.username,
            password: formData.password,
            user_type: formData.user_type
        };
        
        // 如果是学生用户，需要添加管理用户ID
        if (formData.user_type === '学生用户') {
            if (!formData.manager_id) {
                showMessage('学生用户必须指定管理用户', 'error');
                return;
            }
            requestData.manager_id = parseInt(formData.manager_id);
        }
        
        // 添加联系方式
        if (formData.email) requestData.email = formData.email;
        if (formData.phone) requestData.phone = formData.phone;
        
        await apiRequest('/users/', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });
        showMessage('用户创建成功', 'success');
        closeModal('userModal');
        loadUsers();
    } catch (error) {
        showMessage('创建用户失败: ' + error.message, 'error');
    }
}

// 创建用户（保留向后兼容）
async function createUser(username, password, userType) {
    try {
        await apiRequest('/users/', {
            method: 'POST',
            body: JSON.stringify({
                username,
                password,
                user_type: userType
            })
        });
        showMessage('用户创建成功', 'success');
        loadUsers();
    } catch (error) {
        showMessage('创建用户失败: ' + error.message, 'error');
    }
}

