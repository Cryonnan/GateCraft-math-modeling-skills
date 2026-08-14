---
name: linear-regression-hw
description: 回归分析作业助手，涵盖数据预处理、异常值检测、OLS回归、Breusch-Pagan异方差检验、Durbin-Watson自相关检验、WLS/GLS处理
---

# 回归分析作业助手

## 触发词
- "回归分析"、"回归作业"
- "一元线性回归"
- "异常值"、"异方差"、"自相关"
- 直接发送数据文件

---

# 标准建模流程

## Step 1 数据读取
```r
library(readxl)
data <- read_excel("数据文件.xlsx", sheet = "Sheet1")
```

## Step 2 初步OLS回归
```r
lm_model <- lm(y ~ x, data = data)
summary(lm_model)
```

## Step 3 散点图与回归线
```r
plot(data$x, data$y, xlab = "x", ylab = "y", main = "散点图", pch = 16, col = "steelblue")
abline(lm_model, col = "red", lwd = 2)
```

## Step 4 异常值检测
```r
sre <- rstandard(lm_model)
cook <- cooks.distance(lm_model)
which(abs(sre) > 2)
which(cook > 4/length(cook))
```

## Step 5 删除异常值（如有）
```r
data_clean <- data[abs(sre) <= 2, ]
lm_clean <- lm(y ~ x, data = data_clean)
summary(lm_clean)
```

## Step 6 残差诊断图
```r
sre_clean <- rstandard(lm_clean)
par(mfrow = c(1, 2))
plot(data_clean$x, sre_clean, xlab = "x", ylab = "学生化残差", main = "残差 vs 自变量", pch = 16, col = "steelblue")
abline(h = 0, col = "red", lwd = 2)
plot(lm_clean$fitted.values, sre_clean, xlab = "预测值", ylab = "学生化残差", main = "残差 vs 预测值", pch = 16, col = "steelblue")
abline(h = 0, col = "red", lwd = 2)
```

## Step 7 异方差检验 Breusch-Pagan
```r
library(lmtest)
bptest(lm_clean)
```
- p < 0.05 → 存在异方差，需要WLS处理
- p > 0.05 → 同方差假设成立

## Step 8 异方差处理 WLS
```r
w <- 1/data_clean$x
lm_wls <- lm(y ~ x, data = data_clean, weights = w)
summary(lm_wls)
```

## Step 9 自相关检验 Durbin-Watson
```r
dwtest(lm_clean)
```
- DW ≈ 2 → 无自相关
- DW < 2 → 正自相关
- p < 0.05 → 显著自相关

## Step 10 自相关处理 GLS
```r
library(nlme)
lm_gls <- gls(y ~ x, data = data_clean, correlation = corAR1())
summary(lm_gls)
```

## Step 11 预测分析
```r
mean(data_clean$x)
range(data_clean$x)
predict(lm_wls, newdata = data.frame(x = 新值))
```

---

# 诊断结论判断

## 异方差处理决策
| BP检验p值 | 结论 | 处理 |
|-----------|------|------|
| p < 0.05 | 存在异方差 | WLS |
| p > 0.05 | 同方差 | 无需处理 |

## 自相关处理决策
| DW检验 | p值 | 结论 | 处理 |
|--------|-----|------|------|
| DW ≈ 2 | p > 0.05 | 无自相关 | 无需处理 |
| DW < 2 | p < 0.05 | 正自相关 | GLS |

## 外推判断
| 情况 | 判断 |
|------|------|
| 新值在范围内 | 可预测 |
| 新值超出范围 | 外推不可靠 |
