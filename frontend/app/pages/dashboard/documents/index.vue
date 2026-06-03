<template>
  <div class="p-8">
    <h1 class="text-3xl font-bold text-foreground mb-6">Documents</h1>
    <p class="text-muted-foreground mb-8">Manage and organize your documents.</p>
    
    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
          <CardDescription>Add a new document to your library</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">Upload PDF, Word, or other document formats.</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Recent Documents</CardTitle>
          <CardDescription>View your recently uploaded files</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">Access your latest documents quickly.</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Document Search</CardTitle>
          <CardDescription>Search through your document library</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">Find documents by name, content, or tags.</p>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
</script>
