<template>
  <div class="min-h-screen bg-background flex flex-col">
    <header class="border-b border-border px-6 py-4">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="text-xl font-bold text-foreground">ClarityDoc</div>
        <div class="flex items-center gap-3">
          <Show when="signed-out">
            <SignInButton class="px-4 py-2 text-sm font-medium text-foreground hover:bg-muted rounded-md transition-colors">
              Sign In
            </SignInButton>
            <SignUpButton class="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 rounded-md transition-opacity">
              Sign Up
            </SignUpButton>
          </Show>
          <Show when="signed-in">
            <NuxtLink to="/dashboard" class="px-4 py-2 text-sm font-medium bg-primary text-primary-foreground hover:opacity-90 rounded-md transition-opacity">
              Go to Dashboard
            </NuxtLink>
            <UserButton />
          </Show>
        </div>
      </div>
    </header>

    <section class="flex-1 flex items-center justify-center px-4">
      <div class="max-w-4xl mx-auto text-center">
      <div class="inline-flex items-center px-4 py-2 rounded-full bg-muted text-muted-foreground text-sm font-medium mb-8">
        <span class="w-2 h-2 rounded-full bg-primary mr-2"></span>
        AI-Native Document Intelligence
      </div>
      
      <h1 class="text-5xl md:text-7xl font-bold text-foreground mb-6 leading-tight">
        Upload any document.<br>
        <span class="text-primary">Understand everything.</span>
      </h1>
      
      <p class="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
        ClarityDoc is your AI-powered document advisor for contracts, NDAs, and legal agreements. Get instant risk analysis, clause comparisons, and plain-English explanations.
      </p>
      
      <div class="flex flex-col sm:flex-row gap-4 justify-center mb-16">
        <button class="px-8 py-4 bg-primary text-primary-foreground rounded-lg font-semibold hover:opacity-90 transition-opacity">
          Get Started Free
        </button>
        <button class="px-8 py-4 bg-secondary text-secondary-foreground rounded-lg font-semibold hover:opacity-90 transition-opacity">
          View Demo
        </button>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="text-center">
          <div class="text-4xl font-bold text-primary mb-2">94%</div>
          <div class="text-muted-foreground text-sm">Accuracy on NDA review</div>
        </div>
        <div class="text-center">
          <div class="text-4xl font-bold text-primary mb-2">60s</div>
          <div class="text-muted-foreground text-sm">Average analysis time</div>
        </div>
        <div class="text-center">
          <div class="text-4xl font-bold text-primary mb-2">$29</div>
          <div class="text-muted-foreground text-sm">Starting at /month</div>
        </div>
      </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
// No dynamic logic needed for static hero section
</script>