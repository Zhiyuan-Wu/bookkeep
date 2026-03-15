/**
 * 统计信息功能
 */

// 存储统计信息数据，用于窗口大小改变时重新渲染
let statisticsData = null;  // 按供应商统计数据
let userStatisticsData = null;  // 按用户统计数据
let currentStatsView = 'supplier';  // 当前视图：'supplier' 或 'user'

// 加载统计信息
async function loadStatistics() {
    try {
        const response = await apiRequest('/statistics/');
        statisticsData = { items: response.items, total: response.total };
        renderStatisticsTable(statisticsData.items, statisticsData.total);
    } catch (error) {
        showMessage('加载统计信息失败: ' + error.message, 'error');
    }
}

// 监听窗口大小改变，重新渲染统计信息
window.addEventListener('resize', () => {
    // 如果当前在统计信息页面且有数据，则重新渲染
    if (currentPage === 'statistics') {
        if (currentStatsView === 'supplier' && statisticsData) {
            renderStatisticsTable(statisticsData.items, statisticsData.total);
        } else if (currentStatsView === 'user' && userStatisticsData) {
            renderUserStatisticsTables();
        }
    }
});

// 渲染统计表格
function renderStatisticsTable(items, total) {
    // 检测是否为移动端
    const isMobile = window.innerWidth <= 768;

    // 查找或创建移动端容器
    let mobileContainer = document.getElementById('statisticsMobileContainer');
    const table = document.querySelector('.stats-table');

    if (isMobile) {
        // 移动端：隐藏表格，显示卡片
        if (table) {
            table.style.display = 'none';
        }

        // 创建移动端容器
        if (!mobileContainer) {
            mobileContainer = document.createElement('div');
            mobileContainer.id = 'statisticsMobileContainer';
            mobileContainer.className = 'cart-items-mobile';
            // 插入到表格后面
            if (table && table.parentNode) {
                table.parentNode.insertBefore(mobileContainer, table.nextSibling);
            }
        }

        let html = '';

        if (items.length === 0) {
            html = '<div class="cart-item-card"><p style="text-align: center; padding: 40px; color: var(--color-muted);">暂无数据</p></div>';
        } else {
            // 渲染各供应商数据
            items.forEach(item => {
                html += `
                    <div class="cart-item-card">
                        <div class="cart-item-header">
                            <span class="cart-item-name">${item.supplier_name}</span>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
                            <div class="stat-row">
                                <span class="stat-label">订单总数</span>
                                <span class="stat-value">${item.order_count}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">商品总数</span>
                                <span class="stat-value">${item.product_count}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">订单总团购价格</span>
                                <span class="stat-value">${formatCurrency(item.total_internal_price)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">订单总含税价格</span>
                                <span class="stat-value">${formatCurrency(item.total_tax_included_price)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">总服务价格</span>
                                <span class="stat-value">${formatCurrency(item.total_service_amount)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">总税额</span>
                                <span class="stat-value">${formatCurrency(item.total_tax)}</span>
                            </div>
                            <div class="stat-row" style="border-top: 2px solid var(--color-primary); padding-top: 8px; margin-top: 4px;">
                                <span class="stat-label" style="color: var(--color-primary); font-weight: 600;">总结余</span>
                                <span class="stat-value" style="color: var(--color-primary); font-weight: 600;">${formatCurrency(item.total_balance)}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            // 渲染总计卡片
            html += `
                <div class="cart-item-card" style="background: rgba(20, 118, 255, 0.08); border-color: var(--color-primary);">
                    <div class="cart-item-header">
                        <span class="cart-item-name" style="color: var(--color-primary);">${total.supplier_name}</span>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
                        <div class="stat-row">
                            <span class="stat-label">订单总数</span>
                            <span class="stat-value"><strong>${total.order_count}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">商品总数</span>
                            <span class="stat-value"><strong>${total.product_count}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">订单总团购价格</span>
                            <span class="stat-value"><strong>${formatCurrency(total.total_internal_price)}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">订单总含税价格</span>
                            <span class="stat-value"><strong>${formatCurrency(total.total_tax_included_price)}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">总服务价格</span>
                            <span class="stat-value"><strong>${formatCurrency(total.total_service_amount)}</strong></span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">总税额</span>
                            <span class="stat-value"><strong>${formatCurrency(total.total_tax)}</strong></span>
                        </div>
                        <div class="stat-row" style="border-top: 2px solid var(--color-primary); padding-top: 8px; margin-top: 4px;">
                            <span class="stat-label" style="color: var(--color-primary); font-weight: 600;">总结余</span>
                            <span class="stat-value" style="color: var(--color-primary); font-weight: 600;"><strong>${formatCurrency(total.total_balance)}</strong></span>
                        </div>
                    </div>
                </div>
            `;
        }

        mobileContainer.innerHTML = html;
        mobileContainer.style.display = 'flex';
    } else {
        // PC端：显示表格，隐藏移动端容器
        if (table) {
            table.style.display = 'table';
        }
        if (mobileContainer) {
            mobileContainer.style.display = 'none';
        }

        const tbody = document.getElementById('statisticsTableBody');
        tbody.innerHTML = '';

        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
            return;
        }

        // 渲染各供应商数据
        items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.supplier_name}</td>
                <td>${item.order_count}</td>
                <td>${item.product_count}</td>
                <td>${formatCurrency(item.total_internal_price)}</td>
                <td>${formatCurrency(item.total_tax_included_price)}</td>
                <td>${formatCurrency(item.total_service_amount)}</td>
                <td>${formatCurrency(item.total_tax)}</td>
                <td>${formatCurrency(item.total_balance)}</td>
            `;
            tbody.appendChild(row);
        });

        // 渲染总计行
        const totalRow = document.createElement('tr');
        totalRow.className = 'total-row';
        totalRow.innerHTML = `
            <td><strong>${total.supplier_name}</strong></td>
            <td><strong>${total.order_count}</strong></td>
            <td><strong>${total.product_count}</strong></td>
            <td><strong>${formatCurrency(total.total_internal_price)}</strong></td>
            <td><strong>${formatCurrency(total.total_tax_included_price)}</strong></td>
            <td><strong>${formatCurrency(total.total_service_amount)}</strong></td>
            <td><strong>${formatCurrency(total.total_tax)}</strong></td>
            <td><strong>${formatCurrency(total.total_balance)}</strong></td>
        `;
        tbody.appendChild(totalRow);
    }
}

// 加载按用户统计
async function loadUserStatistics() {
    try {
        const response = await apiRequest('/statistics/by-user');
        userStatisticsData = {
            groups: response.groups,
            groupTotal: response.group_total,
            details: response.details,
            detailTotal: response.detail_total
        };
        renderUserStatisticsTables();
    } catch (error) {
        showMessage('加载用户统计失败: ' + error.message, 'error');
    }
}

// 渲染用户统计表格
function renderUserStatisticsTables() {
    const isMobile = window.innerWidth <= 768;

    if (isMobile) {
        renderUserStatisticsMobile();
    } else {
        renderUserStatisticsDesktop();
    }
}

// PC端渲染
function renderUserStatisticsDesktop() {
    renderGroupTableDesktop();
    renderUserDetailTableDesktop();
}

// 渲染课题组表格（PC端）
function renderGroupTableDesktop() {
    const tbody = document.getElementById('statsGroupTableBody');
    tbody.innerHTML = '';

    const data = userStatisticsData;

    if (!data || data.groups.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    // 渲染各组数据
    data.groups.forEach(group => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${group.manager_name}</td>
            <td>${group.user_count}</td>
            <td>${group.order_count}</td>
            <td>${group.product_count}</td>
            <td>${formatCurrency(group.total_internal_price)}</td>
            <td>${formatCurrency(group.total_tax_included_price)}</td>
            <td>${formatCurrency(group.total_service_amount)}</td>
            <td>${formatCurrency(group.total_tax)}</td>
            <td>${formatCurrency(group.total_balance)}</td>
        `;
        tbody.appendChild(row);
    });

    // 渲染总计行
    const totalRow = document.createElement('tr');
    totalRow.className = 'total-row';
    totalRow.innerHTML = `
        <td><strong>${data.groupTotal.manager_name}</strong></td>
        <td><strong>${data.groupTotal.user_count}</strong></td>
        <td><strong>${data.groupTotal.order_count}</strong></td>
        <td><strong>${data.groupTotal.product_count}</strong></td>
        <td><strong>${formatCurrency(data.groupTotal.total_internal_price)}</strong></td>
        <td><strong>${formatCurrency(data.groupTotal.total_tax_included_price)}</strong></td>
        <td><strong>${formatCurrency(data.groupTotal.total_service_amount)}</strong></td>
        <td><strong>${formatCurrency(data.groupTotal.total_tax)}</strong></td>
        <td><strong>${formatCurrency(data.groupTotal.total_balance)}</strong></td>
    `;
    tbody.appendChild(totalRow);
}

// 渲染用户详情表格（PC端）
function renderUserDetailTableDesktop() {
    const tbody = document.getElementById('statsUserTableBody');
    tbody.innerHTML = '';

    const data = userStatisticsData;

    if (!data || data.details.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px;">暂无数据</td></tr>';
        return;
    }

    // 按课题组分组用户
    const groupedUsers = {};
    data.details.forEach(user => {
        const groupId = user.group_id;
        if (!groupedUsers[groupId]) {
            groupedUsers[groupId] = {
                groupName: user.group_name,
                users: []
            };
        }
        groupedUsers[groupId].users.push(user);
    });

    // 遍历每个课题组
    Object.keys(groupedUsers).sort((a, b) => {
        // 管理员组(0)放在最后，其他按组名排序
        if (a === '0') return 1;
        if (b === '0') return -1;
        return groupedUsers[a].groupName.localeCompare(groupedUsers[b].groupName);
    }).forEach(groupId => {
        const group = groupedUsers[groupId];

        // 渲染课题组子表头
        const headerRow = document.createElement('tr');
        headerRow.style.background = 'rgba(68, 114, 196, 0.1)';
        headerRow.innerHTML = `
            <td colspan="8" style="padding: 10px 16px; font-weight: 600; color: var(--color-primary);">
                <i class="fas fa-layer-group"></i> ${group.groupName}
            </td>
        `;
        tbody.appendChild(headerRow);

        // 渲染该课题组的用户
        let groupOrderCount = 0;
        let groupProductCount = 0;
        let groupInternalPrice = 0;
        let groupTaxIncludedPrice = 0;
        let groupServiceAmount = 0;
        let groupTax = 0;
        let groupBalance = 0;

        group.users.forEach(user => {
            groupOrderCount += user.order_count;
            groupProductCount += user.product_count;
            groupInternalPrice += user.total_internal_price;
            groupTaxIncludedPrice += user.total_tax_included_price;
            groupServiceAmount += user.total_service_amount;
            groupTax += user.total_tax;
            groupBalance += user.total_balance;

            const row = document.createElement('tr');
            row.innerHTML = `
                <td style="padding-left: 32px;">${user.username}</td>
                <td>${user.order_count}</td>
                <td>${user.product_count}</td>
                <td>${formatCurrency(user.total_internal_price)}</td>
                <td>${formatCurrency(user.total_tax_included_price)}</td>
                <td>${formatCurrency(user.total_service_amount)}</td>
                <td>${formatCurrency(user.total_tax)}</td>
                <td>${formatCurrency(user.total_balance)}</td>
            `;
            tbody.appendChild(row);
        });

        // 渲染课题组小计行
        const subtotalRow = document.createElement('tr');
        subtotalRow.style.background = 'rgba(68, 114, 196, 0.05)';
        subtotalRow.style.fontWeight = '600';
        subtotalRow.innerHTML = `
            <td style="padding-left: 16px;">${group.groupName} 小计</td>
            <td>${groupOrderCount}</td>
            <td>${groupProductCount}</td>
            <td>${formatCurrency(groupInternalPrice)}</td>
            <td>${formatCurrency(groupTaxIncludedPrice)}</td>
            <td>${formatCurrency(groupServiceAmount)}</td>
            <td>${formatCurrency(groupTax)}</td>
            <td>${formatCurrency(groupBalance)}</td>
        `;
        tbody.appendChild(subtotalRow);
    });

    // 渲染总计行
    const totalRow = document.createElement('tr');
    totalRow.className = 'total-row';
    totalRow.innerHTML = `
        <td><strong>${data.detailTotal.username}</strong></td>
        <td><strong>${data.detailTotal.order_count}</strong></td>
        <td><strong>${data.detailTotal.product_count}</strong></td>
        <td><strong>${formatCurrency(data.detailTotal.total_internal_price)}</strong></td>
        <td><strong>${formatCurrency(data.detailTotal.total_tax_included_price)}</strong></td>
        <td><strong>${formatCurrency(data.detailTotal.total_service_amount)}</strong></td>
        <td><strong>${formatCurrency(data.detailTotal.total_tax)}</strong></td>
        <td><strong>${formatCurrency(data.detailTotal.total_balance)}</strong></td>
    `;
    tbody.appendChild(totalRow);
}

// 移动端渲染（简化版，显示卡片）
function renderUserStatisticsMobile() {
    // 隐藏表格
    document.getElementById('statsGroupTable').style.display = 'none';
    document.getElementById('statsUserTable').style.display = 'none';

    // 创建移动端容器
    let mobileContainer = document.getElementById('userStatisticsMobileContainer');
    if (!mobileContainer) {
        mobileContainer = document.createElement('div');
        mobileContainer.id = 'userStatisticsMobileContainer';
        mobileContainer.className = 'cart-items-mobile';
        const container = document.getElementById('statsByUserContainer');
        container.insertBefore(mobileContainer, container.firstChild);
    }

    let html = '';

    // 渲染课题组卡片
    const data = userStatisticsData;

    if (!data || data.groups.length === 0) {
        html = '<div class="cart-item-card"><p style="text-align: center; padding: 40px; color: var(--color-muted);">暂无数据</p></div>';
    } else {
        // 按课题组分组用户
        const groupedUsers = {};
        data.details.forEach(user => {
            const groupId = user.group_id;
            if (!groupedUsers[groupId]) {
                groupedUsers[groupId] = {
                    groupName: user.group_name,
                    users: []
                };
            }
            groupedUsers[groupId].users.push(user);
        });

        // 遍历每个课题组
        Object.keys(groupedUsers).sort((a, b) => {
            if (a === '0') return 1;
            if (b === '0') return -1;
            return groupedUsers[a].groupName.localeCompare(groupedUsers[b].groupName);
        }).forEach(groupId => {
            const group = groupedUsers[groupId];

            // 渲染课题组标题
            html += `
                <div style="background: rgba(68, 114, 196, 0.1); padding: 12px 16px; border-radius: 8px; margin-bottom: 12px; font-weight: 600; color: var(--color-primary);">
                    <i class="fas fa-layer-group"></i> ${group.groupName}
                </div>
            `;

            // 渲染该课题组的用户
            group.users.forEach(user => {
                html += `
                    <div class="cart-item-card">
                        <div class="cart-item-header">
                            <span class="cart-item-name">${user.username}</span>
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
                            <div class="stat-row">
                                <span class="stat-label">订单总数</span>
                                <span class="stat-value">${user.order_count}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">商品总数</span>
                                <span class="stat-value">${user.product_count}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">订单总团购价格</span>
                                <span class="stat-value">${formatCurrency(user.total_internal_price)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">订单总含税价格</span>
                                <span class="stat-value">${formatCurrency(user.total_tax_included_price)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">总服务价格</span>
                                <span class="stat-value">${formatCurrency(user.total_service_amount)}</span>
                            </div>
                            <div class="stat-row">
                                <span class="stat-label">总税额</span>
                                <span class="stat-value">${formatCurrency(user.total_tax)}</span>
                            </div>
                            <div class="stat-row" style="border-top: 2px solid var(--color-primary); padding-top: 8px; margin-top: 4px;">
                                <span class="stat-label" style="color: var(--color-primary); font-weight: 600;">总结余</span>
                                <span class="stat-value" style="color: var(--color-primary); font-weight: 600;">${formatCurrency(user.total_balance)}</span>
                            </div>
                        </div>
                    </div>
                `;
            });
        });
    }

    mobileContainer.innerHTML = html;
    mobileContainer.style.display = 'flex';
}

// 标签页切换初始化
function initStatsTabs() {
    const bySupplierTab = document.getElementById('statsBySupplierTab');
    const byUserTab = document.getElementById('statsByUserTab');
    const bySupplierContainer = document.getElementById('statsBySupplierContainer');
    const byUserContainer = document.getElementById('statsByUserContainer');

    if (!bySupplierTab || !byUserTab) return;

    // 初始化样式
    bySupplierTab.classList.add('active');

    bySupplierTab.addEventListener('click', () => {
        currentStatsView = 'supplier';
        bySupplierTab.classList.add('active');
        byUserTab.classList.remove('active');
        // 更新内联样式
        bySupplierTab.style.borderBottom = '3px solid #4472C4';
        byUserTab.style.borderBottom = 'none';
        bySupplierContainer.style.display = 'block';
        byUserContainer.style.display = 'none';

        // 如果没有数据则加载
        if (!statisticsData) {
            loadStatistics();
        } else {
            renderStatisticsTable(statisticsData.items, statisticsData.total);
        }
    });

    byUserTab.addEventListener('click', () => {
        currentStatsView = 'user';
        byUserTab.classList.add('active');
        bySupplierTab.classList.remove('active');
        // 更新内联样式
        byUserTab.style.borderBottom = '3px solid #4472C4';
        bySupplierTab.style.borderBottom = 'none';
        byUserContainer.style.display = 'block';
        bySupplierContainer.style.display = 'none';

        // 如果没有数据则加载
        if (!userStatisticsData) {
            loadUserStatistics();
        } else {
            renderUserStatisticsTables();
        }
    });
}

document.addEventListener('DOMContentLoaded', initStatsTabs);

