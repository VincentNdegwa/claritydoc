<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, navigateTo } from '#imports'
import { toast } from 'vue-sonner'
import { useAuth } from '@clerk/vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { FileText, Calendar, AlertTriangle, FileIcon, ExternalLink, Brain } from '@lucide/vue'
import { useDocumentApi } from '@/lib/api'
import type { DocumentDetailResponse } from '@/types/api'

interface BreadcrumbItem {
  label: string
  href?: string
}

definePageMeta({
  breadcrumbs: (route: any) => [
    { label: 'Documents', href: '/dashboard/documents' },
    { label: 'Details' }
  ] as BreadcrumbItem[]
})

const route = useRoute()
const { getToken } = useAuth()
const documentApi = useDocumentApi()

const navigateToAnalysis = () => {
  navigateTo(`/dashboard/documents/${documentId.value}/analysis`)
}

const documentDetail = ref<DocumentDetailResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const documentId = computed(() => route.params.id as string)

const statusConfig: Record<string, { bg: string; dot: string; text: string }> = {
  analyzed: { bg: 'bg-green-50 dark:bg-green-950', dot: 'bg-green-500', text: 'text-green-700 dark:text-green-400' },
  processing: { bg: 'bg-blue-50 dark:bg-blue-950', dot: 'bg-blue-500', text: 'text-blue-700 dark:text-blue-400' },
  failed: { bg: 'bg-red-50 dark:bg-red-950', dot: 'bg-red-500', text: 'text-red-700 dark:text-red-400' },
  error: { bg: 'bg-red-50 dark:bg-red-950', dot: 'bg-red-500', text: 'text-red-700 dark:text-red-400' },
  default: { bg: 'bg-muted', dot: 'bg-muted-foreground', text: 'text-muted-foreground' }
}

const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1)

const formatDate = (dateString: string) => 
  new Date(dateString).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })

const fetchDocument = async () => {
  loading.value = true
  error.value = null
  try {
    const token = await getToken.value()
    documentDetail.value = await documentApi.get(documentId.value, token)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch document'
    toast.error('Failed to fetch document')
  } finally {
    loading.value = false
  }
}

onMounted(fetchDocument)
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-foreground">Document Details</h1>
        <p class="text-sm text-muted-foreground mt-0.5">View and manage document information</p>
      </div>
      <Button @click="navigateToAnalysis">
        <Brain class="size-4 mr-2" />
        View Analysis
      </Button>
    </div>

    <div v-if="loading" class="bg-card border rounded-lg p-6 space-y-6">
      <Skeleton class="h-8 w-3/4" />
      <div class="space-y-4">
        <Skeleton class="h-4 w-1/2" />
        <Skeleton class="h-4 w-1/3" />
        <Skeleton class="h-4 w-2/3" />
      </div>
      <div class="grid grid-cols-2 gap-4">
        <Skeleton class="h-20" />
        <Skeleton class="h-20" />
      </div>
    </div>

    <div v-else-if="error" class="bg-card border rounded-lg p-6">
      <div class="text-red-500">{{ error }}</div>
    </div>

    <div v-else-if="documentDetail" class="space-y-6">
      <div class="bg-card border rounded-lg p-6 space-y-6">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-4">
            <div class="size-12 rounded-lg bg-muted flex items-center justify-center">
              <FileText class="size-6 text-muted-foreground" />
            </div>
            <div>
              <h2 class="text-lg font-semibold text-foreground">{{ documentDetail.document.title }}</h2>
              <div class="flex items-center gap-2 mt-2">
                <div :class="statusConfig[documentDetail.document.status]?.bg" class="flex items-center gap-1.5 px-2 py-0.5 rounded">
                  <div :class="statusConfig[documentDetail.document.status]?.dot" class="size-1.5 rounded-full" />
                  <span :class="statusConfig[documentDetail.document.status]?.text" class="text-xs font-medium">{{ capitalize(documentDetail.document.status) }}</span>
                </div>
                <Badge variant="secondary" class="text-xs font-semibold">{{ documentDetail.document.document_type }}</Badge>
              </div>
            </div>
          </div>
        </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="bg-muted/50 rounded-lg p-4">
            <div class="text-2xl font-bold text-foreground">{{ documentDetail.flag_summary.total }}</div>
            <div class="text-sm text-muted-foreground">Total Flags</div>
          </div>
          <div class="bg-muted/50 rounded-lg p-4">
            <div class="text-2xl font-bold text-yellow-600">{{ documentDetail.flag_summary.unresolved }}</div>
            <div class="text-sm text-muted-foreground">Unresolved</div>
          </div>
          <div class="bg-muted/50 rounded-lg p-4">
            <div class="text-2xl font-bold text-green-600">{{ documentDetail.flag_summary.resolved }}</div>
            <div class="text-sm text-muted-foreground">Resolved</div>
          </div>
        </div>
        <div v-if="Object.keys(documentDetail.flag_summary.by_risk_level).length > 0" class="mt-4">
          <div class="text-sm font-medium text-foreground mb-2">By Risk Level</div>
          <div class="flex flex-wrap gap-2">
            <Badge v-for="(count, level) in documentDetail.flag_summary.by_risk_level" :key="level" variant="outline">
              {{ capitalize(level) }}: {{ count }}
            </Badge>
          </div>
        </div>
      </div>


      <div class="bg-card border rounded-lg p-6">
        <h3 class="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
          <FileIcon class="size-5" />
          Document Versions ({{ documentDetail.versions.length }})
        </h3>
        <div v-if="documentDetail.versions.length === 0" class="text-center py-8 text-muted-foreground">
          No versions found for this document.
        </div>
        <div v-else class="space-y-3">
          <div v-for="version in documentDetail.versions" :key="version.id" class="border rounded-lg p-4">
            <div class="flex items-start justify-between">
              <div class="flex items-center gap-3">
                <div class="size-10 rounded-lg bg-muted flex items-center justify-center">
                  <FileText class="size-5 text-muted-foreground" />
                </div>
                <div>
                  <div class="flex items-center gap-2">
                    <span class="text-sm font-medium text-foreground">Version {{ version.version_number }}</span>
                    <Badge v-if="version.is_signed" variant="secondary" class="text-xs">Signed</Badge>
                    <Badge v-if="version.flag_count > 0" variant="outline" class="text-xs">{{ version.flag_count }} flags</Badge>
                  </div>
                  <div class="text-xs text-muted-foreground mt-1">{{ formatDate(version.created_at) }}</div>
                </div>
              </div>
              <Badge variant="secondary" class="text-xs">{{ version.file_type }}</Badge>
            </div>
            <div class="mt-2">
              <a :href="version.storage_path" target="_blank" rel="noopener noreferrer">
                <Button variant="outline" size="sm" class="text-xs">
                  <ExternalLink class="size-3 mr-1" />
                  Open File
                </Button>
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
