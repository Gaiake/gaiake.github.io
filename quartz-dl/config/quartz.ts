import { loadQuartzConfig, loadQuartzLayout } from "./quartz/plugins/loader/config-loader"
import * as ExternalPlugin from "./.quartz/plugins"
import type { ExplorerOptions } from "./.quartz/plugins"

const sortFn: ExplorerOptions["sortFn"] = (a, b) => {
  const chapterNumber = (node: typeof a) => {
    const candidates = [
      node.slugSegment,
      node.displayName,
      typeof node.data?.slug === "string" ? node.data.slug : undefined,
    ]

    for (const value of candidates) {
      const match = value?.match(/第(\d+)章/)
      if (match) {
        return Number(match[1])
      }
    }

    return null
  }

  const aChapter = chapterNumber(a)
  const bChapter = chapterNumber(b)

  if (aChapter !== null && bChapter !== null) {
    return aChapter - bChapter
  }

  if ((!a.isFolder && !b.isFolder) || (a.isFolder && b.isFolder)) {
    return a.displayName.localeCompare(b.displayName, undefined, {
      numeric: true,
      sensitivity: "base",
    })
  }

  return a.isFolder ? -1 : 1
}

ExternalPlugin.Explorer({
  sortFn,
})

const config = await loadQuartzConfig()
export default config
export const layout = await loadQuartzLayout()
