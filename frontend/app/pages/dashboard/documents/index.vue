<template>
  <div class="space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-semibold text-foreground">Document Vault</h1>
        <p class="text-sm text-muted-foreground mt-0.5">Centralized repository for all ingested and analyzed contract assets.</p>
      </div>
      <Button class="flex items-center gap-2" @click="fileInput?.click()">
        <Upload class="size-4" />
        Upload New Document
      </Button>
    </div>
    
    <div class="bg-card border rounded-lg px-4 py-3 flex items-center gap-3 flex-wrap">
      <div class="relative flex-1" style="min-width: 200px;">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-muted-foreground pointer-events-none" />
        <Input type="text" placeholder="Semantic search across all documents…" class="w-full pl-8 pr-3 py-1.5" />
      </div>
      
      <Select>
        <SelectTrigger class="w-[120px]">
          <SelectValue placeholder="Type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All</SelectItem>
          <SelectItem value="nda">NDA</SelectItem>
          <SelectItem value="msa">MSA</SelectItem>
          <SelectItem value="sla">SLA</SelectItem>
          <SelectItem value="sow">SOW</SelectItem>
        </SelectContent>
      </Select>
      
      <Select>
        <SelectTrigger class="w-[120px]">
          <SelectValue placeholder="Risk" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All</SelectItem>
          <SelectItem value="critical">Critical</SelectItem>
          <SelectItem value="high">High</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="clear">Clear</SelectItem>
        </SelectContent>
      </Select>
      
      <Select>
        <SelectTrigger class="w-[120px]">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All</SelectItem>
          <SelectItem value="processing">Processing</SelectItem>
          <SelectItem value="analyzed">Analyzed</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
        </SelectContent>
      </Select>
      
      <div class="flex border rounded overflow-hidden ml-auto">
        <Button variant="ghost" size="sm" class="px-3 py-1.5 bg-primary text-primary-foreground">
          <LayoutGrid class="size-4" />
        </Button>
        <Button variant="ghost" size="sm" class="px-3 py-1.5">
          <List class="size-4" />
        </Button>
      </div>
    </div>
    
    <div class="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-primary/50 hover:bg-muted/50 transition-colors" @click="fileInput?.click()">
      <input ref="fileInput" type="file" class="hidden" accept=".pdf,.docx,.doc" @change="handleFileUpload" />
      <CloudUpload class="size-8 mx-auto mb-3 text-muted-foreground" />
      <div class="text-sm font-medium text-foreground">Drag PDF or DOCX files here, or click to browse</div>
      <div class="text-xs text-muted-foreground mt-1">Max file size 50MB · Supports PDF, DOCX, DOC · All data encrypted at rest with AES-256</div>
    </div>
    
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 6" :key="i" class="bg-card border rounded-lg p-4">
        <div class="flex items-start justify-between mb-3">
          <Skeleton class="size-9 rounded" />
          <Skeleton class="size-8 rounded" />
        </div>
        <Skeleton class="h-4 w-3/4 mb-3" />
        <div class="flex items-center gap-2 mb-3">
          <Skeleton class="h-5 w-20 rounded-full" />
          <Skeleton class="h-5 w-24 rounded-full" />
        </div>
        <Skeleton class="h-3 w-1/2" />
      </div>
    </div>
    <div v-else-if="error" class="flex items-center justify-center py-12">
      <div class="text-red-500">{{ error }}</div>
    </div>
    <div v-else-if="documents.length === 0" class="flex items-center justify-center py-12">
      <div class="text-muted-foreground">No documents found. Upload your first document to get started.</div>
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-4">
      <DocumentCard
        v-for="doc in documents"
        :key="doc.id"
        :doc="doc"
        :status-config="statusConfig"
        :capitalize="capitalize"
        :format-date="formatDate"
        @view="handleView"
        @analyse="handleAnalyse"
        @delete="handleDeleteClick"
      />
    </div>
    <ConfirmDialog
      v-model:open="deleteDialogOpen"
      title="Delete Document"
      :description="deleteDialogDescription"
      confirm-text="Delete"
      cancel-text="Cancel"
      variant="destructive"
      @confirm="handleDeleteConfirm"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { navigateTo } from '#app'
import { toast } from 'vue-sonner'
import { useAuth } from '@clerk/vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DocumentCard from './components/DocumentCard.vue'
import { Search, Upload, LayoutGrid, List, CloudUpload } from '@lucide/vue'
import { useDocumentApi } from '@/lib/api'
import type { DocumentResponse } from '@/types/api'

interface BreadcrumbItem {
  label: string
  href?: string
}

definePageMeta({
  breadcrumbs: () => [{ label: 'Documents' }] as BreadcrumbItem[]
})

const MAX_FILE_SIZE = 50 * 1024 * 1024
const VALID_FILE_TYPES = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']

const documents = ref<DocumentResponse[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const deleteDialogOpen = ref(false)
const documentToDelete = ref<DocumentResponse | null>(null)

const { getToken } = useAuth()
const documentApi = useDocumentApi()

const statusConfig: Record<string, { bg: string; dot: string; text: string }> = {
  analyzed: { bg: 'bg-green-50 dark:bg-green-950', dot: 'bg-green-500', text: 'text-green-700 dark:text-green-400' },
  processing: { bg: 'bg-blue-50 dark:bg-blue-950', dot: 'bg-blue-500', text: 'text-blue-700 dark:text-blue-400' },
  failed: { bg: 'bg-red-50 dark:bg-red-950', dot: 'bg-red-500', text: 'text-red-700 dark:text-red-400' },
  error: { bg: 'bg-red-50 dark:bg-red-950', dot: 'bg-red-500', text: 'text-red-700 dark:text-red-400' },
  default: { bg: 'bg-muted', dot: 'bg-muted-foreground', text: 'text-muted-foreground' }
}

const documentTypeMap: Record<string, string> = {
  nda: 'NDA',
  msa: 'MSA',
  sla: 'SLA',
  sow: 'SOW'
}

const fetchDocuments = async () => {
  loading.value = true
  error.value = null
  try {
    const token = await getToken.value()
    documents.value = await documentApi.list(token)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to fetch documents'
    toast.error('Failed to fetch documents')
  } finally {
    loading.value = false
  }
}

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return

  if (file.size > MAX_FILE_SIZE) {
    toast.error('File size exceeds 50MB limit')
    return
  }

  if (!VALID_FILE_TYPES.includes(file.type)) {
    toast.error('Invalid file type. Please upload PDF or DOCX files.')
    return
  }

  const filename = file.name.toLowerCase()
  const documentType = Object.entries(documentTypeMap).find(([key]) => filename.includes(key))?.[1] || 'OTHER'

  uploading.value = true
  try {
    const token = await getToken.value()
    await documentApi.upload({ file, document_type: documentType }, token)
    await fetchDocuments()
    fileInput.value && (fileInput.value.value = '')
    toast.success('Document uploaded successfully')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'Failed to upload document')
  } finally {
    uploading.value = false
  }
}

const handleView = (doc: DocumentResponse) => {
  navigateTo(`/dashboard/documents/${doc.id}`)
}

const handleAnalyse = (doc: DocumentResponse) => {
  navigateTo(`/dashboard/documents/${doc.id}/analysis`)
}

const handleDeleteClick = (doc: DocumentResponse) => {
  documentToDelete.value = doc
  deleteDialogOpen.value = true
}

const deleteDialogDescription = computed(() => 
  documentToDelete.value ? `Are you sure you want to delete "${documentToDelete.value.title}"? This action cannot be undone.` : ''
)

const handleDeleteConfirm = async () => {
  if (!documentToDelete.value) return
  
  try {
    const token = await getToken.value()
    await documentApi.delete(documentToDelete.value.id, token)
    toast.success('Document deleted successfully')
    await fetchDocuments()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'Failed to delete document')
  } finally {
    documentToDelete.value = null
  }
}

const capitalize = (str: string) => str.charAt(0).toUpperCase() + str.slice(1)

const formatDate = (dateString: string) => 
  new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

onMounted(fetchDocuments)
</script>
