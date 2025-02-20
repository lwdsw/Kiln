import { init, register, waitLocale } from "svelte-i18n"

register("en", () => import("./locales/en.json"))
register("zh", () => import("./locales/zh.json"))

// 获取初始语言
const getInitialLocale = () => {
  const savedLocale = localStorage.getItem("lang")
  if (savedLocale) return savedLocale

  const browserLocale = navigator.language.split("-")[0]
  return ["zh", "en"].includes(browserLocale) ? browserLocale : "en"
}

// 初始化函数
const initI18n = () => {
  init({
    fallbackLocale: "zh",
    initialLocale: getInitialLocale(),
  })
}

// 确保在浏览器环境下运行
if (typeof window !== "undefined") {
  initI18n()
}

export { waitLocale }
