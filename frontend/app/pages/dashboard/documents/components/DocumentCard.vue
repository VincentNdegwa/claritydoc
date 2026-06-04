<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { FileText, MoreHorizontal, Eye, Brain, Trash2 } from '@lucide/vue'
import type { DocumentResponse } from '@/types/api'

interface Props {
  doc: DocumentResponse
  statusConfig: Record<string, { bg: string; dot: string; text: string }>
  capitalize: (str: string) => string
  formatDate: (dateString: string) => string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  view: [doc: DocumentResponse]
  analyse: [doc: DocumentResponse]
  delete: [doc: DocumentResponse]
}>()

const handleView = () => {
  emit('view', props.doc)
}

const handleAnalyse = () => {
  emit('analyse', props.doc)
}

const handleDelete = () => {
  emit('delete', props.doc)
}
</script>

<template>
  <div class="bg-card border rounded-lg p-4 hover:border-primary/50 hover:shadow-sm transition-all cursor-pointer group">
    <div class="flex items-start justify-between mb-3">
      <div class="size-9 rounded bg-muted flex items-center justify-center shrink-0">
        <FileText class="size-4 text-muted-foreground" />
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button variant="ghost" size="sm" class="p-1.5 h-auto text-muted-foreground">
            <MoreHorizontal class="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem @click="handleView">
            <Eye class="size-4 mr-2" />
            View
          </DropdownMenuItem>
          <DropdownMenuItem @click="handleAnalyse">
            <Brain class="size-4 mr-2" />
            Analyse
          </DropdownMenuItem>
          <DropdownMenuItem @click="handleDelete" class="text-destructive">
            <Trash2 class="size-4 mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
    <div class="text-xs font-medium text-foreground truncate mb-1">{{ doc.title }}</div>
    <div class="flex items-center gap-2 mb-3">
      <div :class="statusConfig[doc.status]?.bg" class="flex items-center gap-1.5 px-2 py-0.5 rounded">
        <div :class="statusConfig[doc.status]?.dot" class="size-1.5 rounded-full" />
        <span :class="statusConfig[doc.status]?.text" class="text-xs font-medium">{{ capitalize(doc.status) }}</span>
      </div>
      <Badge variant="secondary" class="text-xs font-semibold flex items-center overflow-hidden max-w-[190px] shrink-0">
        <span class="truncate">{{ doc.document_type }}</span>
      </Badge>
    </div>
    <div class="text-xs text-muted-foreground mb-3">{{ formatDate(doc.created_at) }}</div>
  </div>
</template>
