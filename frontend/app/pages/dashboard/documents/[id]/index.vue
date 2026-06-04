<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute } from "#imports";
import { toast } from "vue-sonner";
import { useAuth } from "@clerk/vue";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  BookOpen,
  ShieldAlert,
  FileSearch,
  Hash,
  CalendarClock,
  Tag,
} from "@lucide/vue";
import { useDocumentApi } from "@/lib/api";
import DocumentChatPanel from "@/pages/dashboard/documents/components/DocumentChatPanel.vue";
import type {
  DeepAnalysisViewResponse,
  DocumentChunkPreviewResponse,
  ObligationResponse,
} from "@/types/api";
import MarkdownIt from "markdown-it";

const md = new MarkdownIt();

interface BreadcrumbItem {
  label: string;
  href?: string;
}

definePageMeta({
  breadcrumbs: (route: any) =>
    [
      { label: "Documents", href: "/dashboard/documents" },
      { label: "Details", href: `/dashboard/documents/${route.params.id}` },
      { label: "Analysis" },
    ] as BreadcrumbItem[],
});

const route = useRoute();
const documentId = computed(() => route.params.id as string);
const { getToken } = useAuth();
const documentApi = useDocumentApi();

const analysis = ref<DeepAnalysisViewResponse | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const chunkMap = computed<Record<string, DocumentChunkPreviewResponse>>(() => {
  if (!analysis.value) return {};
  return Object.fromEntries(analysis.value.chunk_preview.map((c) => [c.id, c]));
});

const obligationsByChunk = computed<Record<string, ObligationResponse[]>>(() => {
  if (!analysis.value) return {};
  return analysis.value.obligations.reduce(
    (acc, o) => {
      const key = o.document_chunk_id || "general";
      (acc[key] ??= []).push(o);
      return acc;
    },
    {} as Record<string, ObligationResponse[]>
  );
});

const riskConfig: Record<string, { border: string; bg: string; text: string; dot: string }> = {
  critical: {
    border: "border-l-red-500",
    bg: "bg-red-50 dark:bg-red-950/30",
    text: "text-red-700 dark:text-red-400",
    dot: "bg-red-500",
  },
  high: {
    border: "border-l-orange-500",
    bg: "bg-orange-50 dark:bg-orange-950/30",
    text: "text-orange-700 dark:text-orange-400",
    dot: "bg-orange-500",
  },
  medium: {
    border: "border-l-yellow-500",
    bg: "bg-yellow-50 dark:bg-yellow-950/20",
    text: "text-yellow-700 dark:text-yellow-400",
    dot: "bg-yellow-500",
  },
  low: {
    border: "border-l-green-500",
    bg: "bg-green-50 dark:bg-green-950/20",
    text: "text-green-700 dark:text-green-400",
    dot: "bg-green-500",
  },
  clear: {
    border: "border-l-blue-500",
    bg: "bg-blue-50 dark:bg-blue-950/20",
    text: "text-blue-700 dark:text-blue-400",
    dot: "bg-blue-500",
  },
  default: {
    border: "border-l-border",
    bg: "bg-muted/30",
    text: "text-muted-foreground",
    dot: "bg-muted-foreground",
  },
};

const flagStatusConfig: Record<string, { bg: string; text: string }> = {
  open: { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-700 dark:text-yellow-400" },
  resolved: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-700 dark:text-green-400" },
  dismissed: { bg: "bg-muted", text: "text-muted-foreground" },
  default: { bg: "bg-muted", text: "text-muted-foreground" },
};

const obligationStatusConfig: Record<string, { bg: string; text: string; icon: any }> = {
  pending: { bg: "bg-yellow-100 dark:bg-yellow-900/30", text: "text-yellow-700 dark:text-yellow-400", icon: Clock },
  completed: { bg: "bg-green-100 dark:bg-green-900/30", text: "text-green-700 dark:text-green-400", icon: CheckCircle },
  overdue: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-700 dark:text-red-400", icon: AlertTriangle },
  default: { bg: "bg-muted", text: "text-muted-foreground", icon: Clock },
};

const riskLevelOrder = ["critical", "high", "medium", "low", "clear"];

const capitalize = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
const formatCategory = (s: string) => s.split("_").map(capitalize).join(" ");

const fetchAnalysis = async () => {
  loading.value = true;
  error.value = null;
  try {
    const token = await getToken.value();
    analysis.value = await documentApi.getAnalysis(documentId.value, token);
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Failed to fetch analysis";
    toast.error("Failed to fetch analysis");
  } finally {
    loading.value = false;
  }
};

onMounted(fetchAnalysis);
</script>

<template>
  <div class="space-y-6 max-w-5xl">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-foreground tracking-tight">Document Analysis</h1>
        <p class="text-sm text-muted-foreground mt-0.5">AI-extracted audit flags and contractual obligations</p>
      </div>
    </div>

    <div v-if="loading" class="space-y-4">
      <Skeleton class="h-36 rounded-xl" />
      <Skeleton class="h-10 rounded-lg" />
      <Skeleton class="h-64 rounded-xl" />
    </div>

    <div v-else-if="error" class="border border-destructive/30 bg-destructive/5 rounded-xl p-6 flex items-start gap-3">
      <AlertTriangle class="size-5 text-destructive shrink-0 mt-0.5" />
      <p class="text-sm text-destructive">{{ error }}</p>
    </div>

    <template v-else-if="analysis">
      <div class="bg-card border rounded-xl p-5">
        <div class="flex items-start gap-4 mb-5">
          <div class="size-11 rounded-lg bg-muted flex items-center justify-center shrink-0">
            <FileText class="size-5 text-muted-foreground" />
          </div>
          <div class="min-w-0 flex-1">
            <h2 class="text-base font-semibold text-foreground truncate">{{ analysis.document.title }}</h2>
            <div class="flex items-center flex-wrap gap-2 mt-1.5">
              <Badge variant="secondary" class="text-xs">{{ analysis.document.document_type }}</Badge>
              <Badge variant="outline" class="text-xs">v{{ analysis.active_version.version_number }}</Badge>
              <Badge variant="outline" class="text-xs capitalize">{{ analysis.document.status }}</Badge>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="rounded-lg border bg-muted/30 p-3.5">
            <div class="text-2xl font-bold text-foreground tabular-nums">{{ analysis.flag_summary.total }}</div>
            <div class="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
              <ShieldAlert class="size-3" /> Total Flags
            </div>
          </div>
          <div class="rounded-lg border bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-900/40 p-3.5">
            <div class="text-2xl font-bold text-yellow-700 dark:text-yellow-400 tabular-nums">{{ analysis.flag_summary.unresolved }}</div>
            <div class="text-xs text-yellow-600 dark:text-yellow-500 mt-0.5">Unresolved</div>
          </div>
          <div class="rounded-lg border bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900/40 p-3.5">
            <div class="text-2xl font-bold text-green-700 dark:text-green-400 tabular-nums">{{ analysis.flag_summary.resolved }}</div>
            <div class="text-xs text-green-600 dark:text-green-500 mt-0.5">Resolved</div>
          </div>
          <div class="rounded-lg border bg-muted/30 p-3.5">
            <div class="text-2xl font-bold text-foreground tabular-nums">{{ analysis.obligation_count }}</div>
            <div class="text-xs text-muted-foreground mt-0.5 flex items-center gap-1">
              <BookOpen class="size-3" /> Obligations
            </div>
          </div>
        </div>

        <div v-if="Object.keys(analysis.flag_summary.by_risk_level).length > 0" class="mt-4 pt-4 border-t">
          <p class="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-2.5">Risk Breakdown</p>
          <div class="flex flex-wrap gap-2">
            <div
              v-for="level in riskLevelOrder.filter(l => analysis!.flag_summary.by_risk_level[l])"
              :key="level"
              class="flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium border"
              :class="[riskConfig[level]?.bg, riskConfig[level]?.text]"
            >
              <span :class="riskConfig[level]?.dot" class="size-1.5 rounded-full inline-block" />
              {{ capitalize(level) }} · {{ analysis.flag_summary.by_risk_level[level] }}
            </div>
          </div>
        </div>
      </div>

      <Tabs default-value="flags" class="w-full">
        <TabsList class="h-10 p-1 bg-muted/50 border rounded-lg w-full grid grid-cols-2">
          <TabsTrigger value="flags" class="rounded-md text-sm gap-2">
            <AlertTriangle class="size-3.5" />
            Audit Flags
            <span class="ml-1 bg-muted text-muted-foreground rounded px-1.5 py-0.5 text-xs font-mono">
              {{ analysis.flags.length }}
            </span>
          </TabsTrigger>
          <TabsTrigger value="obligations" class="rounded-md text-sm gap-2">
            <CheckCircle class="size-3.5" />
            Obligations
            <span class="ml-1 bg-muted text-muted-foreground rounded px-1.5 py-0.5 text-xs font-mono">
              {{ analysis.obligation_count }}
            </span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="flags" class="mt-4">
          <div v-if="analysis.flags.length === 0" class="bg-card border rounded-xl p-12 text-center">
            <ShieldAlert class="size-8 text-muted-foreground/40 mx-auto mb-3" />
            <p class="text-sm text-muted-foreground">No audit flags found for this document.</p>
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="flag in analysis.flags"
              :key="flag.id"
              class="bg-card border border-l-4 rounded-xl p-4 transition-shadow hover:shadow-sm"
              :class="riskConfig[flag.risk_level]?.border || riskConfig.default!.border"
            >
              <div class="flex items-start justify-between gap-3 mb-2.5">
                <div class="flex items-center flex-wrap gap-1.5">
                  <span
                    class="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold"
                    :class="[riskConfig[flag.risk_level]?.bg, riskConfig[flag.risk_level]?.text]"
                  >
                    <span :class="riskConfig[flag.risk_level]?.dot" class="size-1.5 rounded-full" />
                    {{ capitalize(flag.risk_level) }}
                  </span>
                  <Badge variant="outline" class="text-xs flex items-center gap-1">
                    <Tag class="size-2.5" />
                    {{ formatCategory(flag.category) }}
                  </Badge>
                  <span
                    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                    :class="[flagStatusConfig[flag.status]?.bg, flagStatusConfig[flag.status]?.text]"
                  >
                    {{ capitalize(flag.status) }}
                  </span>
                </div>
                <Popover v-if="flag.document_chunk_id && chunkMap[flag.document_chunk_id]">
                  <PopoverTrigger as-child>
                    <Button variant="ghost" size="sm" class="h-7 px-2 text-xs shrink-0 text-muted-foreground gap-1">
                      <FileSearch class="size-3" />
                      Citation
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent class="w-96 max-h-80 overflow-auto">
                    <div class="space-y-2.5">
                      <div class="flex items-center gap-2 text-sm font-semibold">
                        <Hash class="size-3.5 text-muted-foreground" />
                        Section {{ (chunkMap[flag.document_chunk_id!]?.chunk_index ?? 0) + 1 }}
                        <span v-if="chunkMap[flag.document_chunk_id!]?.page_number" class="text-xs font-normal text-muted-foreground ml-auto">
                          p. {{ chunkMap[flag.document_chunk_id!]?.page_number }}
                        </span>
                      </div>
                      <p v-if="chunkMap[flag.document_chunk_id!]?.heading" class="text-xs font-medium text-foreground">
                        {{ chunkMap[flag.document_chunk_id!]?.heading }}
                      </p>
                      <Separator />
                      <p class="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">
                        {{ chunkMap[flag.document_chunk_id!]?.preview_text }}
                      </p>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>

              <h3 class="text-sm font-semibold text-foreground mb-1.5">{{ flag.issue_summary }}</h3>
              <div
                class="text-sm text-muted-foreground prose prose-sm dark:prose-invert max-w-none"
                v-html="md.render(flag.detailed_explanation)"
              />

              <div v-if="flag.playbook_counter_proposal" class="mt-3 rounded-lg border border-dashed bg-muted/30 p-3.5">
                <p class="text-xs font-semibold text-foreground mb-1.5 flex items-center gap-1.5">
                  <BookOpen class="size-3 text-muted-foreground" />
                  Suggested Counter Proposal
                </p>
                <div
                  class="text-sm text-muted-foreground prose prose-sm dark:prose-invert max-w-none"
                  v-html="md.render(flag.playbook_counter_proposal)"
                />
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="obligations" class="mt-4">
          <div v-if="analysis.obligations.length === 0" class="bg-card border rounded-xl p-12 text-center">
            <BookOpen class="size-8 text-muted-foreground/40 mx-auto mb-3" />
            <p class="text-sm text-muted-foreground">No obligations found for this document.</p>
          </div>
          <div v-else class="space-y-6">
            <div v-for="(obligations, chunkId) in obligationsByChunk" :key="chunkId">
              <div class="flex items-center gap-2 mb-3">
                <div v-if="chunkId !== 'general'" class="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  <Hash class="size-3.5" />
                  Section {{ (chunkMap[chunkId]?.chunk_index ?? 0) + 1 }}
                  <span v-if="chunkMap[chunkId]?.heading" class="normal-case font-normal text-muted-foreground">
                    — {{ chunkMap[chunkId]?.heading }}
                  </span>
                </div>
                <div v-else class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  General Obligations
                </div>
              </div>

              <div class="space-y-3">
                <div
                  v-for="obligation in obligations"
                  :key="obligation.id"
                  class="bg-card border rounded-xl p-4 hover:shadow-sm transition-shadow"
                >
                  <div class="flex items-start justify-between gap-3 mb-2.5">
                    <div class="flex items-center gap-2">
                      <component
                        :is="obligationStatusConfig[obligation.status]?.icon || obligationStatusConfig.default!.icon"
                        class="size-4 shrink-0"
                        :class="obligationStatusConfig[obligation.status]?.text || obligationStatusConfig.default!.text"
                      />
                      <span
                        class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                        :class="[
                          obligationStatusConfig[obligation.status]?.bg || obligationStatusConfig.default!.bg,
                          obligationStatusConfig[obligation.status]?.text || obligationStatusConfig.default!.text,
                        ]"
                      >
                        {{ capitalize(obligation.status) }}
                      </span>
                    </div>
                    <Popover v-if="obligation.document_chunk_id && chunkMap[obligation.document_chunk_id]">
                      <PopoverTrigger as-child>
                        <Button variant="ghost" size="sm" class="h-7 px-2 text-xs shrink-0 text-muted-foreground gap-1">
                          <FileSearch class="size-3" />
                          Citation
                        </Button>
                      </PopoverTrigger>
                      <PopoverContent class="w-96 max-h-80 overflow-auto">
                        <div class="space-y-2.5">
                          <div class="flex items-center gap-2 text-sm font-semibold">
                            <Hash class="size-3.5 text-muted-foreground" />
                            Section {{ (chunkMap[obligation.document_chunk_id!]?.chunk_index ?? 0) + 1 }}
                            <span v-if="chunkMap[obligation.document_chunk_id!]?.page_number" class="text-xs font-normal text-muted-foreground ml-auto">
                              p. {{ chunkMap[obligation.document_chunk_id!]?.page_number }}
                            </span>
                          </div>
                          <p v-if="chunkMap[obligation.document_chunk_id!]?.heading" class="text-xs font-medium text-foreground">
                            {{ chunkMap[obligation.document_chunk_id!]?.heading }}
                          </p>
                          <Separator />
                          <p class="text-xs text-muted-foreground leading-relaxed whitespace-pre-wrap">
                            {{ chunkMap[obligation.document_chunk_id!]?.preview_text }}
                          </p>
                        </div>
                      </PopoverContent>
                    </Popover>
                  </div>

                  <h3 class="text-sm font-semibold text-foreground mb-1.5">{{ obligation.title }}</h3>
                  <div
                    v-if="obligation.description"
                    class="text-sm text-muted-foreground prose prose-sm dark:prose-invert max-w-none"
                    v-html="md.render(obligation.description)"
                  />
                  <div v-if="obligation.due_date" class="mt-2.5 flex items-center gap-1.5 text-xs text-muted-foreground">
                    <CalendarClock class="size-3.5" />
                    Due {{ obligation.due_date }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>

      <DocumentChatPanel
        :document-id="analysis.document.id"
        :flags="analysis.flags"
        :obligations="analysis.obligations"
        :format-category="formatCategory"
        :capitalize="capitalize"
      />
    </template>
  </div>
</template>