<template>
  <div class="p-8">
    <h1 class="text-3xl font-bold text-foreground mb-6">Dashboard</h1>
    <p class="text-muted-foreground mb-8">Welcome to your ClarityDoc dashboard.</p>
    
    <div class="grid gap-6 md:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
          <CardDescription>Manage your documents</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">View and organize all your documents in one place.</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Audits</CardTitle>
          <CardDescription>Document audits</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">Track and review document compliance audits.</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Obligations</CardTitle>
          <CardDescription>Compliance obligations</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">Monitor and manage regulatory obligations.</p>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
</script>