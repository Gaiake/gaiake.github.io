import { loadQuartzConfig, loadQuartzLayout } from "./quartz/plugins/loader/config-loader"
import * as ExternalPlugin from "./.quartz/plugins"
import type { ExplorerOptions } from "./.quartz/plugins"

const sortFn: ExplorerOptions["sortFn"] = (a, b) => {
  const aCandidates = [
    a.slugSegment,
    a.displayName,
    typeof a.data?.slug === "string" ? a.data.slug : undefined,
  ]
  const bCandidates = [
    b.slugSegment,
    b.displayName,
    typeof b.data?.slug === "string" ? b.data.slug : undefined,
  ]

  let aChapter: number | null = null
  let bChapter: number | null = null

  for (const value of aCandidates) {
    const match = value?.match(/第(\d+)章/)
    if (match) {
      aChapter = Number(match[1])
      break
    }
  }

  for (const value of bCandidates) {
    const match = value?.match(/第(\d+)章/)
    if (match) {
      bChapter = Number(match[1])
      break
    }
  }

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
