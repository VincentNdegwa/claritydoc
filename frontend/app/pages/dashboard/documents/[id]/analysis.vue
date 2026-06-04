<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute } from "#imports";
import { toast } from "vue-sonner";
import { useAuth } from "@clerk/vue";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  FileText,
  AlertTriangle,
  FileText as FileIcon,
  Calendar,
  FileText as FileTextIcon,
  CheckCircle,
  Clock,
} from "@lucide/vue";
import { useDocumentApi } from "@/lib/api";
import type {
  DeepAnalysisViewResponse,
  AuditFlagResponse,
  DocumentChunkPreviewResponse,
  ObligationResponse,
} from "@/types/api";
import MarkdownIt from 'markdown-it'

const md = new MarkdownIt()

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
  const map: Record<string, DocumentChunkPreviewResponse> = {};
  for (const chunk of analysis.value.chunk_preview) {
    map[chunk.id] = chunk;
  }
  return map;
});

const obligationsByChunk = computed<Record<string, ObligationResponse[]>>(() => {
  if (!analysis.value) return {};
  const map: Record<string, ObligationResponse[]> = {};
  for (const obligation of analysis.value.obligations) {
    const chunkId = obligation.document_chunk_id || 'general';
    if (!map[chunkId]) {
      map[chunkId] = [];
    }
    map[chunkId].push(obligation);
  }
  return map;
});

const riskLevelConfig: Record<string, { bg: string; text: string }> = {
  critical: {
    bg: "bg-red-100 dark:bg-red-900",
    text: "text-red-700 dark:text-red-400",
  },
  high: {
    bg: "bg-orange-100 dark:bg-orange-900",
    text: "text-orange-700 dark:text-orange-400",
  },
  medium: {
    bg: "bg-yellow-100 dark:bg-yellow-900/30",
    text: "text-yellow-700 dark:text-yellow-400",
  },
  low: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-700 dark:text-green-400",
  },
  clear: {
    bg: "bg-blue-100 dark:bg-blue-900/30",
    text: "text-blue-700 dark:text-blue-400",
  },
  default: { bg: "bg-muted", text: "text-muted-foreground" },
};

const statusConfig: Record<string, { bg: string; text: string }> = {
  open: {
    bg: "bg-yellow-100 dark:bg-yellow-900/30",
    text: "text-yellow-700 dark:text-yellow-400",
  },
  resolved: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-700 dark:text-green-400",
  },
  dismissed: {
    bg: "bg-gray-100 dark:bg-gray-900/30",
    text: "text-gray-700 dark:text-gray-400",
  },
  default: { bg: "bg-muted", text: "text-muted-foreground" },
};

const obligationStatusConfig: Record<string, { bg: string; text: string; icon: any }> = {
  pending: {
    bg: "bg-yellow-100 dark:bg-yellow-900/30",
    text: "text-yellow-700 dark:text-yellow-400",
    icon: Clock,
  },
  completed: {
    bg: "bg-green-100 dark:bg-green-900/30",
    text: "text-green-700 dark:text-green-400",
    icon: CheckCircle,
  },
  overdue: {
    bg: "bg-red-100 dark:bg-red-900/30",
    text: "text-red-700 dark:text-red-400",
    icon: AlertTriangle,
  },
  default: { bg: "bg-muted", text: "text-muted-foreground", icon: Clock },
};

const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1);

const formatCategory = (str: string) => {
  return str
    .split('_')
    .map(word => capitalize(word))
    .join(' ');
};

const fetchAnalysis = async () => {
  loading.value = true;
  error.value = null;
  try {
    const token = await getToken.value();
    analysis.value = await documentApi.getAnalysis(documentId.value, token);
  } catch (err) {
    error.value =
      err instanceof Error ? err.message : "Failed to fetch analysis";
    toast.error("Failed to fetch analysis");
  } finally {
    loading.value = false;
  }
};

onMounted(fetchAnalysis);
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-xl font-semibold text-foreground">Document Analysis</h1>
      <p class="text-sm text-muted-foreground mt-0.5">
        Deep analysis and audit flags for the document
      </p>
    </div>

    <div v-if="loading" class="space-y-6">
      <Skeleton class="h-32" />
      <Skeleton class="h-48" />
      <Skeleton class="h-64" />
    </div>

    <div v-else-if="error" class="bg-card border rounded-lg p-6">
      <div class="text-red-500">{{ error }}</div>
    </div>

    <div v-else-if="analysis" class="space-y-6">
      <div class="bg-card border rounded-lg p-6">
        <h2 class="text-lg font-semibold text-foreground mb-4">
          Document Overview
        </h2>
        <div class="flex items-center gap-4 mb-4">
          <div
            class="size-12 rounded-lg bg-muted flex items-center justify-center"
          >
            <FileText class="size-6 text-muted-foreground" />
          </div>
          <div>
            <h3 class="text-base font-medium text-foreground">
              {{ analysis.document.title }}
            </h3>
            <div class="flex items-center gap-2 mt-1">
              <Badge variant="secondary" class="text-xs">{{
                analysis.document.document_type
              }}</Badge>
              <Badge variant="outline" class="text-xs"
                >Version {{ analysis.active_version.version_number }}</Badge
              >
            </div>
          </div>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="bg-muted/50 rounded-lg p-4">
            <div class="text-2xl font-bold text-foreground">
              {{ analysis.flag_summary.total }}
            </div>
            <div class="text-sm text-muted-foreground">Total Flags</div>
          </div>
          <div class="bg-muted/50 rounded-lg p-4">
            <div class="text-2xl font-bold text-yellow-600">
              {{ analysis.flag_summary.unresolved }}
            </div>
            <div class="text-sm text-muted-foreground">Unresolved</div>
          </div>
          <div class="bg-muted/50 rounded-lg p-4">
            <div class="text-2xl font-bold text-green-600">
              {{ analysis.flag_summary.resolved }}
            </div>
            <div class="text-sm text-muted-foreground">Resolved</div>
          </div>
          <div class="bg-muted/50 rounded-lg p-4">
            <div class="text-2xl font-bold text-foreground">
              {{ analysis.obligation_count }}
            </div>
            <div class="text-sm text-muted-foreground">Obligations</div>
          </div>
        </div>
        <div
          v-if="Object.keys(analysis.flag_summary.by_risk_level).length > 0"
          class="mt-4"
        >
          <div class="text-sm font-medium text-foreground mb-2">
            By Risk Level
          </div>
          <div class="flex flex-wrap gap-2">
            <Badge
              v-for="(count, level) in analysis.flag_summary.by_risk_level"
              :key="level"
              variant="outline"
            >
              {{ capitalize(level) }}: {{ count }}
            </Badge>
          </div>
        </div>
      </div>

      <Tabs default-value="flags" class="w-full">
        <TabsList class="grid w-full grid-cols-2">
          <TabsTrigger value="flags">
            <AlertTriangle class="size-4 mr-2" />
            Audit Flags ({{ analysis.flags.length }})
          </TabsTrigger>
          <TabsTrigger value="obligations">
            <CheckCircle class="size-4 mr-2" />
            Obligations ({{ analysis.obligation_count }})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="flags" class="mt-6">
          <div class="bg-card border rounded-lg p-6">
            <div
              v-if="analysis.flags.length === 0"
              class="text-center py-8 text-muted-foreground"
            >
              No audit flags found for this document.
            </div>
            <div v-else class="space-y-4">
              <div
                v-for="flag in analysis.flags"
                :key="flag.id"
                class="border rounded-lg p-4"
              >
                <div class="flex items-start justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <Badge
                      :class="[riskLevelConfig[flag.risk_level]?.bg, riskLevelConfig[flag.risk_level]?.text]"
                      class="text-xs font-medium"
                    >
                      {{ capitalize(flag.risk_level) }}
                    </Badge>
                    <Badge variant="outline" class="text-xs">{{
                      formatCategory(flag.category)
                    }}</Badge>
                    <Badge :class="[statusConfig[flag.status]?.bg, statusConfig[flag.status]?.text]" class="text-xs">
                      {{ capitalize(flag.status) }}
                    </Badge>
                  </div>
                  <Popover
                    v-if="
                      flag.document_chunk_id && chunkMap[flag.document_chunk_id]
                    "
                  >
                    <PopoverTrigger as-child>
                      <Button variant="ghost" size="sm" class="text-xs">
                        <FileTextIcon class="size-3 mr-1" />
                        View Citation
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent class="w-96 max-h-96 overflow-auto">
                      <div class="space-y-2">
                        <div class="flex items-center gap-2 text-sm font-medium">
                          <FileTextIcon class="size-4" />
                          Section {{ (chunkMap[flag.document_chunk_id!]?.chunk_index ?? 0) + 1 }}
                        </div>
                        <div
                          v-if="chunkMap[flag.document_chunk_id!]?.heading"
                          class="text-xs text-muted-foreground"
                        >
                          {{ chunkMap[flag.document_chunk_id!]?.heading }}
                        </div>
                        <div
                          v-if="chunkMap[flag.document_chunk_id!]?.page_number"
                          class="text-xs text-muted-foreground"
                        >
                          Page {{ chunkMap[flag.document_chunk_id!]?.page_number }}
                        </div>
                        <div
                          class="text-sm text-muted-foreground whitespace-pre-wrap"
                        >
                          {{ chunkMap[flag.document_chunk_id!]?.preview_text }}
                        </div>
                      </div>
                    </PopoverContent>
                  </Popover>
                </div>
                <h3 class="text-sm font-medium text-foreground mb-1">
                  {{ flag.issue_summary }}
                </h3>
                <div class="text-sm text-muted-foreground mb-2 prose prose-sm dark:prose-invert max-w-none" v-html="md.render(flag.detailed_explanation)"></div>
                <div
                  v-if="flag.playbook_counter_proposal"
                  class="bg-muted/50 rounded p-3 mt-2"
                >
                  <div class="text-xs font-medium text-foreground mb-1">
                    Counter Proposal
                  </div>
                  <div class="text-sm text-muted-foreground prose prose-sm dark:prose-invert max-w-none" v-html="md.render(flag.playbook_counter_proposal)"></div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="obligations" class="mt-6">
          <div class="bg-card border rounded-lg p-6">
            <div
              v-if="analysis.obligations.length === 0"
              class="text-center py-8 text-muted-foreground"
            >
              No obligations found for this document.
            </div>
            <div v-else class="space-y-6">
              <div
                v-for="(obligations, chunkId) in obligationsByChunk"
                :key="chunkId"
                class="space-y-3"
              >
                <div v-if="chunkId !== 'general'" class="flex items-center gap-2 text-sm font-medium text-foreground mb-3">
                  <FileTextIcon class="size-4" />
                  Section {{ (chunkMap[chunkId]?.chunk_index ?? 0) + 1 }}
                  <span v-if="chunkMap[chunkId]?.heading" class="text-muted-foreground">- {{ chunkMap[chunkId]?.heading }}</span>
                </div>
                <div v-else class="text-sm font-medium text-foreground mb-3">
                  General Obligations
                </div>
                <div class="space-y-3">
                  <div
                    v-for="obligation in obligations"
                    :key="obligation.id"
                    class="border rounded-lg p-4"
                  >
                    <div class="flex items-start justify-between mb-2">
                      <div class="flex items-center gap-2">
                        <component
                          :is="obligationStatusConfig[obligation.status]?.icon || obligationStatusConfig.default!.icon"
                          class="size-4"
                          :class="obligationStatusConfig[obligation.status]?.text || obligationStatusConfig.default!.text"
                        />
                        <Badge
                          :class="[obligationStatusConfig[obligation.status]?.bg, obligationStatusConfig[obligation.status]?.text]"
                          class="text-xs font-medium"
                        >
                          {{ capitalize(obligation.status) }}
                        </Badge>
                      </div>
                      <Popover
                        v-if="obligation.document_chunk_id && chunkMap[obligation.document_chunk_id]"
                      >
                        <PopoverTrigger as-child>
                          <Button variant="ghost" size="sm" class="text-xs">
                            <FileTextIcon class="size-3 mr-1" />
                            View Citation
                          </Button>
                        </PopoverTrigger>
                        <PopoverContent class="w-96 max-h-96 overflow-auto">
                          <div class="space-y-2">
                            <div class="flex items-center gap-2 text-sm font-medium">
                              <FileTextIcon class="size-4" />
                              Section {{ (chunkMap[obligation.document_chunk_id!]?.chunk_index ?? 0) + 1 }}
                            </div>
                            <div
                              v-if="chunkMap[obligation.document_chunk_id!]?.heading"
                              class="text-xs text-muted-foreground"
                            >
                              {{ chunkMap[obligation.document_chunk_id!]?.heading }}
                            </div>
                            <div
                              v-if="chunkMap[obligation.document_chunk_id!]?.page_number"
                              class="text-xs text-muted-foreground"
                            >
                              Page {{ chunkMap[obligation.document_chunk_id!]?.page_number }}
                            </div>
                            <div
                              class="text-sm text-muted-foreground whitespace-pre-wrap"
                            >
                              {{ chunkMap[obligation.document_chunk_id!]?.preview_text }}
                            </div>
                          </div>
                        </PopoverContent>
                      </Popover>
                    </div>
                    <h3 class="text-sm font-medium text-foreground mb-1">
                      {{ obligation.title }}
                    </h3>
                    <div class="text-sm text-muted-foreground mb-2 prose prose-sm dark:prose-invert max-w-none" v-html="md.render(obligation.description)"></div>
                    <div v-if="obligation.due_date" class="text-xs text-muted-foreground">
                      Due: {{ obligation.due_date }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  </div>
</template>
