<template>
  <div class="p-8">
    <h1 class="text-3xl font-bold text-foreground mb-6">Commitments</h1>
    <p class="text-muted-foreground mb-8">Track and manage your contractual commitments and obligations.</p>
    
    <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Deadlines</CardTitle>
          <CardDescription>View approaching commitment deadlines</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">Monitor critical dates and renewal windows.</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Obligation Tracker</CardTitle>
          <CardDescription>Track contractual obligations</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">Ensure all obligations are met on time.</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>Calendar View</CardTitle>
          <CardDescription>Visual timeline of commitments</CardDescription>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground">View commitments in a calendar format.</p>
        </CardContent>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
</script>
