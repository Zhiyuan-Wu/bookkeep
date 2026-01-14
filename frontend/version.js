/**
 * 前端资源版本号配置
 *
 * 说明：此文件用于集中管理前端资源的版本号
 * 当前端代码更新后，修改此处的版本号，然后在HTML文件中全局替换
 *
 * 使用方法：
 * 1. 修改下面的 VERSION 值，例如从 '1.0.0' 改为 '1.0.1'
 * 2. 在 index.html 和 main.html 中全局替换 ?v=1.0.1 为 ?v=1.0.1
 */

const VERSION = '1.0.0';

// 如果需要在JS代码中动态生成带版本号的URL，可以使用此函数
function getVersionedUrl(url) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}v=${VERSION}`;
}
