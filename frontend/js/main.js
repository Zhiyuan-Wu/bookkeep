/**
 * 主界面初始化
 */

let currentUser = null;
let currentPage = 'products';

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 检查登录状态
    const user = await window.checkAuth();
    if (!user) {
        window.location.href = '/';
        return;
    }
    
    currentUser = user;
    initUI();
    initNavigation();
    loadProducts();
});

// 初始化UI
function initUI() {
    // 设置用户信息
    document.getElementById('userName').textContent = currentUser.username;
    document.getElementById('userType').textContent = currentUser.user_type;
    document.getElementById('userAvatar').textContent = currentUser.username.charAt(0).toUpperCase();
    
    // 根据用户类型显示/隐藏功能
    if (currentUser.user_type === '供应商') {
        document.getElementById('cartBtn').style.display = 'none';
        document.getElementById('statisticsNav').style.display = 'none';
    } else if (currentUser.user_type === '普通用户') {
        document.getElementById('cartBtn').style.display = 'inline-flex';
        document.getElementById('statisticsNav').style.display = 'none';  // 普通用户不能查看统计信息
    } else {
        document.getElementById('cartBtn').style.display = 'inline-flex';
        document.getElementById('statisticsNav').style.display = 'flex';
    }
    
    // 购物车按钮
    document.getElementById('cartBtn').addEventListener('click', () => {
        openCartModal();
    });
    
    // 商品管理按钮
    if (currentUser.user_type === '管理员' || currentUser.user_type === '供应商') {
        document.getElementById('productsActions').style.display = 'flex';
    }
    
    // 服务记录按钮
    if (currentUser.user_type === '供应商') {
        document.getElementById('servicesActions').style.display = 'flex';
    }
    
    // 用户管理
    if (currentUser.user_type === '管理员') {
        document.getElementById('usersManagementCard').style.display = 'block';
        loadUsers();
    }
    
    // 内部价格列（供应商用户和普通用户不显示）
    if (currentUser.user_type === '供应商' || currentUser.user_type === '普通用户') {
        document.getElementById('internalPriceHeader').style.display = 'none';
    } else {
        document.getElementById('internalPriceHeader').style.display = 'table-cell';
    }
    
    // 普通用户不能查看统计信息
    if (currentUser.user_type === '普通用户') {
        document.getElementById('statisticsNav').style.display = 'none';
    }
}

// 初始化导航
function initNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            switchPage(page);
        });
    });
}

// 切换页面
function switchPage(page) {
    // 更新导航状态
    document.querySelectorAll('.sidebar-nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-page="${page}"]`).classList.add('active');
    
    // 更新页面显示
    document.querySelectorAll('.page-content').forEach(content => {
        content.style.display = 'none';
    });
    document.getElementById(`${page}Page`).style.display = 'block';
    
    currentPage = page;
    
    // 加载对应页面数据
    switch (page) {
        case 'products':
            loadProducts();
            break;
        case 'orders':
            if (typeof loadOrderSuppliers === 'function') {
                loadOrderSuppliers();
            }
            loadOrders();
            break;
        case 'services':
            if (typeof loadServiceSuppliers === 'function') {
                loadServiceSuppliers();
            }
            loadServices();
            break;
        case 'statistics':
            loadStatistics();
            break;
        case 'settings':
            // 设置页面不需要加载数据
            break;
    }

    // 同步移动端底部导航高亮
    const mobileNavItems = document.querySelectorAll('.mobile-bottom-nav .nav-item');
    mobileNavItems.forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });
}

// ==================== 移动端侧边栏切换 ====================
const hamburgerBtn = document.getElementById('hamburgerBtn');
const sidebar = document.querySelector('.sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');

function toggleSidebar() {
    if (sidebar && sidebarOverlay) {
        sidebar.classList.toggle('open');
        sidebarOverlay.style.display = sidebar.classList.contains('open') ? 'block' : 'none';
    }
}

function closeSidebar() {
    if (sidebar && sidebarOverlay) {
        sidebar.classList.remove('open');
        sidebarOverlay.style.display = 'none';
    }
}

if (hamburgerBtn) {
    hamburgerBtn.addEventListener('click', toggleSidebar);
}

if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', closeSidebar);
}

// ==================== 移动端底部导航切换 ====================
const mobileNavItems = document.querySelectorAll('.mobile-bottom-nav .nav-item');
mobileNavItems.forEach(item => {
    item.addEventListener('click', () => {
        const page = item.dataset.page;
        switchPage(page);
        closeSidebar(); // 如果侧边栏打开，关闭它
    });
});

// ==================== 移动端购物车按钮 ====================
const mobileCartBtn = document.getElementById('mobileCartBtn');
if (mobileCartBtn) {
    mobileCartBtn.addEventListener('click', () => {
        if (typeof openCartModal === 'function') {
            openCartModal();
        }
    });
}

