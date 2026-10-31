# 把代码推到 Gitee / GitHub（给任何人看都能照做）

本地仓库已经建好，历史完整。只差最后一步：建一个公开仓库，把代码推上去。

---

## 方式一：让队友或老师帮忙（最省事）

把这段话直接发给对方：

> 帮我建一个公开仓库，名字 `campus-lost-found`，然后把地址发我。
> 代码在这台电脑的 `D:\Users\周冠晨\Desktop\拾光里共享版`，
> 双击里面的 `推送代码.bat`，粘贴仓库地址，按提示输入账号密码就行。

---

## 方式二：Gitee（国内，推荐自己操作）

1. 打开 <https://gitee.com/>，右上角「注册」，用手机号注册并登录
2. 右上角「+」→「新建仓库」
   - 仓库名称：`campus-lost-found`
   - 是否开源：**公开**
   - 其他不用改，点「创建」
3. 创建成功后，页面上有一行仓库地址，形如
   `https://gitee.com/你的用户名/campus-lost-found.git`，复制它
4. 回到电脑，双击 `推送代码.bat`
   - 粘贴地址，回车
   - 提示用户名：填 Gitee 用户名
   - 提示密码：填 Gitee 登录密码
5. 看到 `main -> main` 就是成功

---

## 方式三：GitHub

1. 打开 <https://github.com/> 注册并登录
2. 右上角「+」→「New repository」
   - 名称：`campus-lost-found`
   - 选 **Public**
   - 不要勾 README / .gitignore / license
   - 点「Create repository」
3. 复制仓库地址（https 形式）
4. 双击 `推送代码.bat`，粘贴地址
5. **密码不能填登录密码**，要填 Personal Access Token：
   - 头像 → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Generate new token → 勾 `repo` → 生成 → 复制 `ghp_...`
   - 推送时密码处粘这个 token

---

## 推送成功后检查

- 浏览器打开仓库地址，能看到 `README.md`、`server.py`、`用户端.html`
- 仓库里搜不到 `sk-`
- 提交记录能看到 4 条以上

---

## 如果暂时不想弄

不影响开发。本地 Git 会持续记录，最后提交前推一次即可。
把本文件发给能操作的人，5 分钟就能完成。
