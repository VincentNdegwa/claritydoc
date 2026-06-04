<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted, onBeforeUnmount } from "vue";
import { toast } from "vue-sonner";
import { useAuth } from "@clerk/vue";
import MarkdownIt from "markdown-it";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useDocumentApi } from "@/lib/api";
import {
  AlertTriangle,
  CheckCircle,
  Send,
  Paperclip,
  X,
  Bot,
  User,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  Maximize2,
  Minimize2,
} from "@lucide/vue";
import type {
  AuditFlagResponse,
  ObligationResponse,
  DocumentChatRequest,
  DocumentChatResponse,
} from "@/types/api";

interface Props {
  documentId: string;
  flags: AuditFlagResponse[];
  obligations: ObligationResponse[];
  formatCategory: (category: string) => string;
  capitalize: (value: string) => string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  flag_ids?: string[];
  obligation_ids?: string[];
  timestamp: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: "reference-select", payload: { type: "flag" | "obligation"; id: string }): void;
}>();
const { getToken } = useAuth();
const documentApi = useDocumentApi();
const md = new MarkdownIt({ html: true, linkify: true, breaks: true });

const chatMessages = ref<ChatMessage[]>([]);
const chatQuestion = ref("");
const selectedFlagIds = ref<string[]>([]);
const selectedObligationIds = ref<string[]>([]);
const chatLoading = ref(false);
const scrollRef = ref<HTMLElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);
const isOpen = ref(true);
const isMaximized = ref(false);
const showPalette = ref(false);
const paletteQuery = ref("");
const paletteMode = ref<"flags" | "obligations" | null>(null);
const paletteRef = ref<HTMLElement | null>(null);
const REFERENCE_RE = /\{(flag|obligation):([0-9a-f-]{36})\}/g;

const flagMap = computed<Record<string, AuditFlagResponse>>(() =>
  props.flags.reduce(
    (acc, f) => ({ ...acc, [f.id]: f }),
    {} as Record<string, AuditFlagResponse>,
  ),
);

const obligationMap = computed<Record<string, ObligationResponse>>(() =>
  props.obligations.reduce(
    (acc, o) => ({ ...acc, [o.id]: o }),
    {} as Record<string, ObligationResponse>,
  ),
);

interface InlineRef {
  type: "flag" | "obligation";
  id: string;
  label: string;
  meta: string;
  missing: boolean;
}

const buildInlineRef = (type: "flag" | "obligation", id: string): InlineRef => {
  if (type === "flag") {
    const flag = flagMap.value[id];
    if (!flag)
      return { type, id, label: "Unknown flag", meta: "", missing: true };

    return {
      type,
      id,
      label: flag.issue_summary,
      meta: [props.capitalize(flag.risk_level), props.formatCategory(flag.category)].filter(Boolean).join(" · "),
      missing: false,
    };
  }

  const ob = obligationMap.value[id];
  if (!ob)
    return { type, id, label: "Unknown obligation", meta: "", missing: true };

  return {
    type,
    id,
    label: ob.title,
    meta: [props.capitalize(ob.status), ob.due_date ? `Due ${ob.due_date}` : null]
      .filter(Boolean)
      .join(" · "),
    missing: false,
  };
};

const renderMessageContent = (content: string): string => {
  const tokenized = content.replace(REFERENCE_RE, (_match, type, id) => {
    const ref = buildInlineRef(type as "flag" | "obligation", id);
    const colorClass = ref.missing
      ? "clarity-ref--missing"
      : type === "flag"
      ? "clarity-ref--flag"
      : "clarity-ref--obligation";
    const icon = type === "flag" ? "⚑" : "◎";

    return `<span class="clarity-ref ${colorClass}" data-type="${type}" data-id="${id}"><span class="clarity-ref__icon">${icon}</span><span class="clarity-ref__label">${ref.label ?? ""}</span>${ref.meta ? `<span class="clarity-ref__meta">${ref.meta}</span>` : ""}</span>`;
  });

  return md.render(tokenized);
};

const handleReferenceClick = (event: Event) => {
  const target = event.target as HTMLElement | null;
  if (!target) return;
  const refEl = target.closest?.(".clarity-ref") as HTMLElement | null;
  if (!refEl) return;
  const type = refEl.dataset.type as "flag" | "obligation" | undefined;
  const id = refEl.dataset.id;
  if (!type || !id) return;
  emit("reference-select", { type, id });
};

const addReferenceListener = (el: HTMLElement | null) => {
  el?.addEventListener("click", handleReferenceClick);
};

const removeReferenceListener = (el: HTMLElement | null) => {
  el?.removeEventListener("click", handleReferenceClick);
};

watch(scrollRef, (newEl, oldEl) => {
  if (oldEl !== newEl) {
    removeReferenceListener(oldEl || null);
    addReferenceListener(newEl || null);
  }
});

onMounted(() => addReferenceListener(scrollRef.value));
onBeforeUnmount(() => removeReferenceListener(scrollRef.value));

const selectedAttachmentCount = computed(
  () => selectedFlagIds.value.length + selectedObligationIds.value.length,
);

const canSend = computed(
  () => chatQuestion.value.trim().length >= 3 && !chatLoading.value,
);

const paletteItems = computed(() => {
  const q = paletteQuery.value.toLowerCase();
  if (paletteMode.value === "flags") {
    return props.flags
      .filter(
        (f) =>
          f.issue_summary.toLowerCase().includes(q) ||
          f.category.toLowerCase().includes(q),
      )
      .slice(0, 6);
  }
  if (paletteMode.value === "obligations") {
    return props.obligations
      .filter((o) => o.title.toLowerCase().includes(q))
      .slice(0, 6);
  }
  return [];
});

const paletteCommands = [
  {
    id: "flags",
    label: "Attach audit flag",
    icon: "flag",
    description: "Ground response with a flag",
  },
  {
    id: "obligations",
    label: "Attach obligation",
    icon: "obligation",
    description: "Reference an obligation",
  },
];

const filteredCommands = computed(() =>
  paletteCommands.filter((c) =>
    c.label.toLowerCase().includes(paletteQuery.value.toLowerCase()),
  ),
);

const createId = () =>
  `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
const formatTime = (ts: string) =>
  new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const toggleFlag = (id: string) => {
  selectedFlagIds.value = selectedFlagIds.value.includes(id)
    ? selectedFlagIds.value.filter((f) => f !== id)
    : [...selectedFlagIds.value, id];
};

const toggleObligation = (id: string) => {
  selectedObligationIds.value = selectedObligationIds.value.includes(id)
    ? selectedObligationIds.value.filter((o) => o !== id)
    : [...selectedObligationIds.value, id];
};

const clearAttachments = () => {
  selectedFlagIds.value = [];
  selectedObligationIds.value = [];
};

const scrollToBottom = async () => {
  await nextTick();
  scrollRef.value?.scrollTo({
    top: scrollRef.value.scrollHeight,
    behavior: "smooth",
  });
};

const togglePanel = async () => {
  isOpen.value = !isOpen.value;
  if (!isOpen.value) {
    closePalette();
    return;
  }
  await scrollToBottom();
};

const toggleMaximize = async () => {
  isMaximized.value = !isMaximized.value;
  await nextTick();
  await scrollToBottom();
};

const handleTextareaInput = (e: Event) => {
  const target = e.target as HTMLTextAreaElement;
  const val = target.value;
  const lastChar = val.slice(-1);
  const slashIndex = val.lastIndexOf("/");

  if (lastChar === "/") {
    showPalette.value = true;
    paletteMode.value = null;
    paletteQuery.value = "";
    return;
  }

  if (showPalette.value && slashIndex !== -1) {
    paletteQuery.value = val.slice(slashIndex + 1);
    return;
  }

  if (!val.includes("/")) {
    closePalette();
  }
};

const selectPaletteMode = (mode: "flags" | "obligations") => {
  paletteMode.value = mode;
  paletteQuery.value = "";
  showPalette.value = true;
  textareaRef.value?.focus();
};

const selectFlag = (flag: AuditFlagResponse) => {
  if (!selectedFlagIds.value.includes(flag.id)) {
    selectedFlagIds.value = [...selectedFlagIds.value, flag.id];
  }
  const slashIndex = chatQuestion.value.lastIndexOf("/");
  if (slashIndex !== -1) {
    chatQuestion.value = chatQuestion.value.slice(0, slashIndex);
  }
  closePalette();
  textareaRef.value?.focus();
};

const selectObligation = (obligation: ObligationResponse) => {
  if (!selectedObligationIds.value.includes(obligation.id)) {
    selectedObligationIds.value = [
      ...selectedObligationIds.value,
      obligation.id,
    ];
  }
  const slashIndex = chatQuestion.value.lastIndexOf("/");
  if (slashIndex !== -1) {
    chatQuestion.value = chatQuestion.value.slice(0, slashIndex);
  }
  closePalette();
  textareaRef.value?.focus();
};

const closePalette = () => {
  showPalette.value = false;
  paletteMode.value = null;
  paletteQuery.value = "";
};

const sendMessage = async () => {
  if (!canSend.value) return;

  const question = chatQuestion.value.trim();
  const timestamp = new Date().toISOString();

  chatMessages.value.push({
    id: createId(),
    role: "user",
    content: question,
    flag_ids: [...selectedFlagIds.value],
    obligation_ids: [...selectedObligationIds.value],
    timestamp,
  });

  chatQuestion.value = "";
  chatLoading.value = true;
  await scrollToBottom();

  try {
    const token = await getToken.value();
    const payload: DocumentChatRequest = { question };
    if (selectedFlagIds.value.length)
      payload.flag_ids = [...selectedFlagIds.value];
    if (selectedObligationIds.value.length)
      payload.obligation_ids = [...selectedObligationIds.value];

    const response = (await documentApi.chatAboutDocument(
      props.documentId,
      payload,
      token,
    )) as DocumentChatResponse;

    const flagSources = response?.sources
      ?.filter((s) => s.type === "flag")
      .map((s) => s.id);
    const obSources = response?.sources
      ?.filter((s) => s.type === "obligation")
      .map((s) => s.id);

    chatMessages.value.push({
      id: createId(),
      role: "assistant",
      content: response?.answer || "I'm still processing that question.",
      flag_ids: flagSources?.length ? flagSources : payload.flag_ids,
      obligation_ids: obSources?.length ? obSources : payload.obligation_ids,
      timestamp: new Date().toISOString(),
    });

    clearAttachments();
    await scrollToBottom();
  } catch (err) {
    toast.error(err instanceof Error ? err.message : "Failed to send message");
  } finally {
    chatLoading.value = false;
  }
};

const handleTextareaKeydown = (e: KeyboardEvent) => {
  if (showPalette.value && e.key === "Escape") {
    e.preventDefault();
    closePalette();
    return;
  }
  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) sendMessage();
};
</script>

<template>
  <div class="fixed bottom-6 right-6 z-40 flex flex-col items-end gap-3">
    <Transition name="fade-slide">
      <div
        v-if="isOpen"
        class="bg-card border rounded-2xl shadow-lg overflow-hidden transition-all duration-300 ease-out flex flex-col"
        :class="
          isMaximized
            ? 'w-[min(760px,calc(100vw-3rem))] h-[min(85vh,calc(100vh-4rem))]'
            : 'w-[360px]'
        "
      >
        <div
          class="px-5 py-4 border-b bg-muted/20 flex items-center justify-between"
        >
          <div class="flex items-center gap-2.5">
            <div
              class="size-7 rounded-md bg-primary/10 flex items-center justify-center"
            >
              <Sparkles class="size-3.5 text-primary" />
            </div>
            <div>
              <h2 class="text-sm font-semibold text-foreground">
                Ask ClarityDoc
              </h2>
              <p class="text-xs text-muted-foreground">
                Ground responses with flags or obligations
              </p>
            </div>
          </div>
          <div class="flex items-center gap-1.5">
            <Badge
              v-if="selectedAttachmentCount > 0"
              variant="secondary"
              class="text-xs gap-1"
            >
              <Paperclip class="size-3" />
              {{ selectedAttachmentCount }}
            </Badge>
            <Button
              variant="ghost"
              size="icon"
              class="size-7 text-muted-foreground"
              :aria-pressed="isMaximized"
              :title="isMaximized ? 'Exit expanded view' : 'Expand panel'"
              @click="toggleMaximize"
            >
              <Maximize2 v-if="!isMaximized" class="size-4" />
              <Minimize2 v-else class="size-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              class="size-7 text-muted-foreground"
              @click="togglePanel"
            >
              <X class="size-4" />
            </Button>
          </div>
        </div>

        <div
          ref="scrollRef"
          class="overflow-y-auto p-4 space-y-4 scroll-smooth transition-all duration-200"
          :class="isMaximized ? 'flex-1 min-h-[320px]' : 'h-72'"
        >
          <div
            v-if="!chatMessages.length"
            class="h-full flex flex-col items-center justify-center text-center gap-2 py-6"
          >
            <div
              class="size-10 rounded-full bg-muted flex items-center justify-center mb-1"
            >
              <Bot class="size-5 text-muted-foreground" />
            </div>
            <p class="text-sm font-medium text-foreground">
              Start a conversation
            </p>
            <p class="text-xs text-muted-foreground max-w-xs">
              Ask follow-up questions about clauses, risks, or obligations.
              Attach context to stay grounded.
            </p>
          </div>

          <template v-else>
            <div v-for="message in chatMessages" :key="message.id">
              <div
                class="flex items-start gap-2.5"
                :class="message.role === 'user' ? 'flex-row-reverse' : ''"
              >
                <div
                  class="size-6 rounded-full flex items-center justify-center shrink-0 mt-0.5"
                  :class="
                    message.role === 'user' ? 'bg-primary/10' : 'bg-muted'
                  "
                >
                  <User
                    v-if="message.role === 'user'"
                    class="size-3.5 text-primary"
                  />
                  <Bot v-else class="size-3.5 text-muted-foreground" />
                </div>
                <div class="max-w-[80%] space-y-1.5">
                  <div
                    class="flex items-center gap-2"
                    :class="message.role === 'user' ? 'flex-row-reverse' : ''"
                  >
                    <span class="text-xs font-medium text-foreground">
                      {{ message.role === "user" ? "You" : "ClarityDoc" }}
                    </span>
                    <span class="text-xs text-muted-foreground">{{
                      formatTime(message.timestamp)
                    }}</span>
                  </div>
                  <div
                    class="rounded-xl px-3.5 py-2.5 text-sm"
                    :class="
                      message.role === 'user'
                        ? 'bg-primary/10 text-foreground rounded-tr-none'
                        : 'bg-muted/50 border text-foreground rounded-tl-none'
                    "
                  >
                    <p
                      v-if="message.role === 'user'"
                      class="whitespace-pre-wrap"
                    >
                      {{ message.content }}
                    </p>
                    <div
                      v-else
                      class="prose prose-sm dark:prose-invert max-w-none clarity-message"
                      v-html="renderMessageContent(message.content)"
                    />
                  </div>
                  <div
                    v-if="
                      message.flag_ids?.length || message.obligation_ids?.length
                    "
                    class="flex flex-wrap gap-1.5"
                    :class="message.role === 'user' ? 'justify-end' : ''"
                  >
                    <Badge
                      v-for="fId in message.flag_ids"
                      :key="fId"
                      variant="outline"
                      class="text-xs gap-1 max-w-[200px]"
                    >
                      <AlertTriangle class="size-2.5 shrink-0" />
                      <span class="truncate">{{
                        flagMap[fId]?.issue_summary || "Attached flag"
                      }}</span>
                    </Badge>
                    <Badge
                      v-for="oId in message.obligation_ids"
                      :key="oId"
                      variant="secondary"
                      class="text-xs gap-1 max-w-[200px]"
                    >
                      <CheckCircle class="size-2.5 shrink-0" />
                      <span class="truncate">{{
                        obligationMap[oId]?.title || "Attached obligation"
                      }}</span>
                    </Badge>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="chatLoading" class="flex items-start gap-2.5">
              <div
                class="size-6 rounded-full bg-muted flex items-center justify-center shrink-0 mt-0.5"
              >
                <Bot class="size-3.5 text-muted-foreground" />
              </div>
              <div
                class="bg-muted/50 border rounded-xl rounded-tl-none px-3.5 py-2.5"
              >
                <div class="flex items-center gap-1">
                  <span
                    class="size-1.5 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:0ms]"
                  />
                  <span
                    class="size-1.5 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:150ms]"
                  />
                  <span
                    class="size-1.5 rounded-full bg-muted-foreground/60 animate-bounce [animation-delay:300ms]"
                  />
                </div>
              </div>
            </div>
          </template>
        </div>

        <Separator />

        <div class="relative">
          <Transition name="palette">
            <div
              v-if="showPalette"
              ref="paletteRef"
              class="absolute bottom-full left-3 right-3 mb-2 bg-popover border rounded-xl shadow-lg overflow-hidden z-10"
            >
              <div v-if="!paletteMode">
                <div class="px-3 pt-3 pb-2 border-b">
                  <p
                    class="text-xs font-semibold text-muted-foreground uppercase tracking-wide"
                  >
                    Commands
                  </p>
                  <input
                    v-model="paletteQuery"
                    class="mt-1.5 w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground/60 text-foreground"
                    placeholder="Search commands..."
                    autofocus
                  />
                </div>
                <div class="p-1.5 space-y-0.5">
                  <button
                    v-for="cmd in filteredCommands"
                    :key="cmd.id"
                    class="w-full flex items-center gap-3 px-2.5 py-2 rounded-lg hover:bg-muted text-left transition-colors group"
                    @click="
                      selectPaletteMode(cmd.id as 'flags' | 'obligations')
                    "
                  >
                    <div
                      class="size-7 rounded-md flex items-center justify-center shrink-0"
                      :class="
                        cmd.id === 'flags'
                          ? 'bg-orange-100 dark:bg-orange-950/40'
                          : 'bg-blue-100 dark:bg-blue-950/40'
                      "
                    >
                      <AlertTriangle
                        v-if="cmd.id === 'flags'"
                        class="size-3.5 text-orange-600 dark:text-orange-400"
                      />
                      <CheckCircle
                        v-else
                        class="size-3.5 text-blue-600 dark:text-blue-400"
                      />
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-medium text-foreground">
                        {{ cmd.label }}
                      </p>
                      <p class="text-xs text-muted-foreground">
                        {{ cmd.description }}
                      </p>
                    </div>
                    <ChevronRight
                      class="size-3.5 text-muted-foreground/40 group-hover:text-muted-foreground transition-colors"
                    />
                  </button>
                  <p
                    v-if="!filteredCommands.length"
                    class="px-2.5 py-3 text-xs text-muted-foreground text-center"
                  >
                    No commands found
                  </p>
                </div>
              </div>

              <div v-else>
                <div class="px-3 pt-3 pb-2 border-b flex items-center gap-2">
                  <button
                    class="text-muted-foreground hover:text-foreground transition-colors"
                    @click="
                      paletteMode = null;
                      paletteQuery = '';
                    "
                  >
                    <ChevronLeft class="size-4" />
                  </button>
                  <div
                    class="size-5 rounded flex items-center justify-center shrink-0"
                    :class="
                      paletteMode === 'flags'
                        ? 'bg-orange-100 dark:bg-orange-950/40'
                        : 'bg-blue-100 dark:bg-blue-950/40'
                    "
                  >
                    <AlertTriangle
                      v-if="paletteMode === 'flags'"
                      class="size-3 text-orange-600 dark:text-orange-400"
                    />
                    <CheckCircle
                      v-else
                      class="size-3 text-blue-600 dark:text-blue-400"
                    />
                  </div>
                  <p class="text-xs font-semibold text-foreground flex-1">
                    {{
                      paletteMode === "flags" ? "Audit Flags" : "Obligations"
                    }}
                  </p>
                  <p class="text-xs text-muted-foreground">
                    {{ paletteItems.length }} results
                  </p>
                </div>
                <div class="px-3 py-2 border-b">
                  <input
                    v-model="paletteQuery"
                    class="w-full bg-transparent text-sm outline-none placeholder:text-muted-foreground/60 text-foreground"
                    :placeholder="
                      paletteMode === 'flags'
                        ? 'Search flags...'
                        : 'Search obligations...'
                    "
                    autofocus
                  />
                </div>
                <div class="p-1.5 max-h-44 overflow-y-auto space-y-0.5">
                  <button
                    v-if="paletteMode === 'flags'"
                    v-for="flag in paletteItems as AuditFlagResponse[]"
                    :key="flag.id"
                    class="w-full flex items-start gap-2.5 px-2.5 py-2 rounded-lg hover:bg-muted text-left transition-colors"
                    :class="
                      selectedFlagIds.includes(flag.id)
                        ? 'opacity-50 pointer-events-none'
                        : ''
                    "
                    @click="selectFlag(flag)"
                  >
                    <span
                      class="mt-0.5 size-1.5 rounded-full shrink-0 bg-orange-400"
                    />
                    <div class="min-w-0">
                      <p class="text-xs font-medium text-foreground truncate">
                        {{ flag.issue_summary }}
                      </p>
                      <p class="text-xs text-muted-foreground">
                        {{ props.capitalize(flag.risk_level) }} ·
                        {{ props.formatCategory(flag.category) }}
                      </p>
                    </div>
                    <CheckCircle
                      v-if="selectedFlagIds.includes(flag.id)"
                      class="size-3.5 text-primary shrink-0 mt-0.5 ml-auto"
                    />
                  </button>
                  <button
                    v-if="paletteMode === 'obligations'"
                    v-for="obligation in paletteItems as ObligationResponse[]"
                    :key="obligation.id"
                    class="w-full flex items-start gap-2.5 px-2.5 py-2 rounded-lg hover:bg-muted text-left transition-colors"
                    :class="
                      selectedObligationIds.includes(obligation.id)
                        ? 'opacity-50 pointer-events-none'
                        : ''
                    "
                    @click="selectObligation(obligation)"
                  >
                    <span
                      class="mt-0.5 size-1.5 rounded-full shrink-0 bg-blue-400"
                    />
                    <div class="min-w-0">
                      <p class="text-xs font-medium text-foreground truncate">
                        {{ obligation.title }}
                      </p>
                      <p
                        v-if="obligation.due_date"
                        class="text-xs text-muted-foreground"
                      >
                        Due {{ obligation.due_date }}
                      </p>
                    </div>
                    <CheckCircle
                      v-if="selectedObligationIds.includes(obligation.id)"
                      class="size-3.5 text-primary shrink-0 mt-0.5 ml-auto"
                    />
                  </button>
                  <p
                    v-if="!paletteItems.length"
                    class="px-2.5 py-3 text-xs text-muted-foreground text-center"
                  >
                    No {{ paletteMode }} found
                  </p>
                </div>
              </div>
            </div>
          </Transition>

          <div
            class="mx-3 mb-3 rounded-xl border bg-background transition-shadow focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-0 overflow-hidden"
            :class="showPalette ? 'ring-2 ring-ring' : ''"
          >
            <div
              v-if="selectedAttachmentCount > 0"
              class="flex flex-wrap gap-1.5 px-3 pt-2.5"
            >
              <span
                v-for="fId in selectedFlagIds"
                :key="fId"
                class="inline-flex items-center gap-1 rounded-md bg-orange-100 dark:bg-orange-950/40 border border-orange-200 dark:border-orange-900/50 px-1.5 py-0.5 text-xs text-orange-700 dark:text-orange-400 font-medium max-w-[160px]"
              >
                <AlertTriangle class="size-2.5 shrink-0" />
                <span class="truncate">{{
                  flagMap[fId]?.issue_summary || "Flag"
                }}</span>
                <button
                  class="ml-0.5 hover:text-orange-900 dark:hover:text-orange-200 transition-colors"
                  @click="toggleFlag(fId)"
                >
                  <X class="size-2.5" />
                </button>
              </span>
              <span
                v-for="oId in selectedObligationIds"
                :key="oId"
                class="inline-flex items-center gap-1 rounded-md bg-blue-100 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/50 px-1.5 py-0.5 text-xs text-blue-700 dark:text-blue-400 font-medium max-w-[160px]"
              >
                <CheckCircle class="size-2.5 shrink-0" />
                <span class="truncate">{{
                  obligationMap[oId]?.title || "Obligation"
                }}</span>
                <button
                  class="ml-0.5 hover:text-blue-900 dark:hover:text-blue-200 transition-colors"
                  @click="toggleObligation(oId)"
                >
                  <X class="size-2.5" />
                </button>
              </span>
            </div>

            <textarea
              ref="textareaRef"
              v-model="chatQuestion"
              rows="1"
              class="w-full resize-none bg-transparent px-3 py-2.5 text-sm outline-none placeholder:text-muted-foreground/60 min-h-[38px] max-h-28"
              style="field-sizing: content"
              placeholder="Ask anything… type / to attach context"
              @input="handleTextareaInput"
              @keydown="handleTextareaKeydown"
            />

            <div class="flex items-center justify-between px-2.5 pb-2">
              <div class="flex items-center gap-1">
                <button
                  class="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors hover:bg-muted text-muted-foreground hover:text-foreground"
                  @click="selectPaletteMode('flags')"
                >
                  <AlertTriangle class="size-3 text-orange-500" />
                  Flag
                </button>
                <button
                  class="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium transition-colors hover:bg-muted text-muted-foreground hover:text-foreground"
                  @click="selectPaletteMode('obligations')"
                >
                  <CheckCircle class="size-3 text-blue-500" />
                  Obligation
                </button>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-xs text-muted-foreground/50 hidden sm:block"
                  >⌘↵</span
                >
                <Button
                  size="sm"
                  class="h-7 w-7 p-0 rounded-lg"
                  :disabled="!canSend"
                  @click="sendMessage"
                >
                  <Send class="size-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <Button
      v-if="!isOpen"
      variant="default"
      size="lg"
      class="shadow-lg rounded-full px-4 py-2 gap-2"
      @click="togglePanel"
    >
      <Sparkles class="size-4" />
      Ask ClarityDoc
    </Button>
  </div>
</template>

<style scoped>
:deep(.clarity-message) {
  line-height: 1.6;
}

:deep(.clarity-ref) {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  padding: 1px 7px 1px 5px;
  border-radius: 5px;
  border: 1px solid;
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.6;
  vertical-align: baseline;
  white-space: nowrap;
  max-width: 240px;
  cursor: pointer;
  position: relative;
  top: -0.5px;
}

:deep(.clarity-ref__icon) {
  font-size: 0.65rem;
  opacity: 0.8;
  flex-shrink: 0;
}

:deep(.clarity-ref__label) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
  display: inline-block;
}

:deep(.clarity-ref__meta) {
  font-weight: 400;
  opacity: 0.65;
  font-size: 0.65rem;
  padding-left: 4px;
  border-left: 1px solid currentColor;
}

:deep(.clarity-ref--flag) {
  background: rgb(255 237 213 / 0.6);
  border-color: rgb(251 146 60 / 0.4);
  color: #c2410c;
}

:deep(.dark .clarity-ref--flag) {
  background: rgb(124 45 18 / 0.25);
  border-color: rgb(251 146 60 / 0.25);
  color: #fb923c;
}

:deep(.clarity-ref--obligation) {
  background: rgb(219 234 254 / 0.6);
  border-color: rgb(96 165 250 / 0.4);
  color: #1d4ed8;
}

:deep(.dark .clarity-ref--obligation) {
  background: rgb(30 58 138 / 0.25);
  border-color: rgb(96 165 250 / 0.25);
  color: #60a5fa;
}

:deep(.clarity-ref--missing) {
  background: rgb(243 244 246 / 0.6);
  border-color: rgb(156 163 175 / 0.4);
  color: #6b7280;
  text-decoration: line-through;
}
</style>
