<script setup lang="ts">
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { FileText, MoreHorizontal, Eye, Brain, Trash2, CalendarDays } from "@lucide/vue";
import type { DocumentResponse } from "@/types/api";

interface Props {
  doc: DocumentResponse;
  statusConfig: Record<string, { bg: string; dot: string; text: string }>;
  capitalize: (str: string) => string;
  formatDate: (dateString: string) => string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  view: [doc: DocumentResponse];
  analyse: [doc: DocumentResponse];
  delete: [doc: DocumentResponse];
}>();
</script>

<template>
  <div
    class="group bg-card border rounded-xl p-4 flex flex-col gap-3 hover:border-primary/40 hover:shadow-sm transition-all cursor-pointer"
    @click="emit('view', doc)"
  >
    <div class="flex items-start justify-between">
      <div class="size-9 rounded-lg bg-muted flex items-center justify-center shrink-0">
        <FileText class="size-4 text-muted-foreground" />
      </div>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <Button
            variant="ghost"
            size="sm"
            class="h-7 w-7 p-0 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity"
            @click.stop
          >
            <MoreHorizontal class="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" class="w-40">
          <DropdownMenuItem @click.stop="emit('view', doc)" class="gap-2">
            <Eye class="size-3.5" /> View details
          </DropdownMenuItem>
          <DropdownMenuItem @click.stop="emit('analyse', doc)" class="gap-2">
            <Brain class="size-3.5" /> Run analysis
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click.stop="emit('delete', doc)" class="gap-2 text-destructive focus:text-destructive">
            <Trash2 class="size-3.5" /> Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>

    <div class="min-w-0">
      <p class="text-sm font-semibold text-foreground truncate leading-snug">{{ doc.title }}</p>
      <p class="text-xs text-muted-foreground truncate mt-0.5">{{ doc.document_type }}</p>
    </div>

    <div class="flex items-center gap-2 flex-wrap">
      <div
        :class="statusConfig[doc.status]?.bg"
        class="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5"
      >
        <span :class="statusConfig[doc.status]?.dot" class="size-1.5 rounded-full" />
        <span :class="statusConfig[doc.status]?.text" class="text-xs font-medium">
          {{ capitalize(doc.status) }}
        </span>
      </div>
    </div>

    <div class="flex items-center gap-1.5 text-xs text-muted-foreground mt-auto pt-1 border-t">
      <CalendarDays class="size-3" />
      {{ formatDate(doc.created_at) }}
    </div>
  </div>
</template>