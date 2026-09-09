# 微信代码上传安全说明

`miniprogram-ci` 仅用于把已验收的 Git 提交上传为微信开发版本，不进入小程序运行包，也不用于普通构建和测试。

截至 2026-09-05，npm 的 `latest` 标签为 `miniprogram-ci@2.1.31`。其传递依赖存在多项已知高危和严重漏洞，且部分没有上游修复版本。因此发布流程采用以下补偿控制：

1. 精确锁定依赖版本并使用 `npm ci --ignore-scripts`，不自动升级或执行依赖安装脚本。
2. 只允许手动触发 GitHub Actions，不在 push 或 pull request 上自动上传。
3. 上传任务绑定 `wechat-upload` Environment；正式使用前必须在 GitHub 中设置 Required reviewers。
4. 上传密钥只保存为 Environment secret `MINIPROGRAM_PRIVATE_KEY`，任务中写入权限为 `0600` 的临时文件，任务结束后由临时运行器销毁。
5. 工作流仅授予仓库内容读取权限，不持有写仓库权限。
6. 上传脚本要求负责人确认标志、固定 AppID、干净工作树以及与当前检出内容完全一致的 40 位 Git commit。
7. 上传任务只处理已审核的受保护分支提交；不得对来自 fork、未知压缩包或未经评审的代码运行。
8. 每次发布前重新执行完整 npm 审计并核对官方稳定版本；如上游发布已修复版本，应先升级、验证再上传。

该流程只上传开发版本，不会自动提交审核或正式发布。生成上传密钥、配置 GitHub secret、首次启用 Environment、实际触发上传都必须由负责人单独确认。
