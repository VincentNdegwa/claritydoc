<template>
  <div>
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Active Contracts Under Mgmt.</p>
              <p class="text-2xl font-bold mt-1">47</p>
              <p class="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                <span class="text-green-600">+3</span> this week
              </p>
            </div>
            <div class="p-2 bg-primary/10 rounded-lg">
              <FileText class="size-5 text-primary" />
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Unresolved Critical Exposure</p>
              <p class="text-2xl font-bold mt-1 text-destructive">8</p>
              <p class="text-xs text-muted-foreground mt-1">Requires immediate legal review</p>
            </div>
            <div class="p-2 bg-destructive/10 rounded-lg">
              <AlertTriangle class="size-5 text-destructive" />
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">Obligations Due ≤ 30 Days</p>
              <p class="text-2xl font-bold mt-1">12</p>
              <p class="text-xs text-muted-foreground mt-1">Next due in 5 days</p>
            </div>
            <div class="p-2 bg-orange-500/10 rounded-lg">
              <Bell class="size-5 text-orange-500" />
            </div>
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardContent class="p-6">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-muted-foreground">AI Cost Accrued This Month</p>
              <p class="text-2xl font-bold mt-1">2,840</p>
              <p class="text-xs text-muted-foreground mt-1">≈ $0.004 / token · 710K tokens used</p>
            </div>
            <div class="p-2 bg-blue-500/10 rounded-lg">
              <Zap class="size-5 text-blue-500" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
    
    <!-- Active Ingestion Pipelines -->
    <Card class="mb-8">
      <CardHeader>
        <div class="flex items-center justify-between">
          <div>
            <CardTitle>Active Ingestion Pipelines</CardTitle>
            <CardDescription>4 running</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div class="flex items-center gap-4">
            <div class="p-2 bg-primary/10 rounded-lg">
              <FileText class="size-4 text-primary" />
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium">Enterprise_SaaS_MSA_Q2.pdf</p>
              <p class="text-xs text-muted-foreground">Parsing text...</p>
            </div>
            <Progress :value="35" class="w-24" />
            <span class="text-sm font-medium w-8">35%</span>
          </div>
          
          <div class="flex items-center gap-4">
            <div class="p-2 bg-primary/10 rounded-lg">
              <FileText class="size-4 text-primary" />
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium">Vendor_NDA_Acme_Corp.docx</p>
              <p class="text-xs text-muted-foreground">Running multi-agent audit...</p>
            </div>
            <Progress :value="72" class="w-24" />
            <span class="text-sm font-medium w-8">72%</span>
          </div>
          
          <div class="flex items-center gap-4">
            <div class="p-2 bg-primary/10 rounded-lg">
              <FileText class="size-4 text-primary" />
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium">SOW_ProjectAlpha_2026.pdf</p>
              <p class="text-xs text-muted-foreground">Extracting timeline...</p>
            </div>
            <Progress :value="88" class="w-24" />
            <span class="text-sm font-medium w-8">88%</span>
          </div>
          
          <div class="flex items-center gap-4">
            <div class="p-2 bg-primary/10 rounded-lg">
              <FileText class="size-4 text-primary" />
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium">Partnership_Agreement_XYZ.pdf</p>
              <p class="text-xs text-muted-foreground">Parsing text...</p>
            </div>
            <Progress :value="14" class="w-24" />
            <span class="text-sm font-medium w-8">14%</span>
          </div>
        </div>
      </CardContent>
    </Card>
    
    <!-- Upcoming Milestones -->
    <Card class="mb-8">
      <CardHeader>
        <div class="flex items-center justify-between">
          <div>
            <CardTitle>Upcoming Milestones</CardTitle>
            <CardDescription>30-day window</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div class="space-y-4">
          <div class="flex items-center gap-4 p-3 rounded-lg border">
            <Badge variant="outline" class="w-12 justify-center">5d</Badge>
            <div class="flex-1">
              <p class="text-sm font-medium">Auto-Renewal Window Closes</p>
              <p class="text-xs text-muted-foreground">SaaS Master Agreement 2025</p>
            </div>
            <AlertTriangle class="size-4 text-orange-500" />
          </div>
          
          <div class="flex items-center gap-4 p-3 rounded-lg border">
            <Badge variant="outline" class="w-12 justify-center">12d</Badge>
            <div class="flex-1">
              <p class="text-sm font-medium">Notice Period for Termination</p>
              <p class="text-xs text-muted-foreground">Vendor NDA — Acme Corp</p>
            </div>
            <Clock class="size-4 text-muted-foreground" />
          </div>
          
          <div class="flex items-center gap-4 p-3 rounded-lg border">
            <Badge variant="outline" class="w-12 justify-center">18d</Badge>
            <div class="flex-1">
              <p class="text-sm font-medium">Annual License Fee Due</p>
              <p class="text-xs text-muted-foreground">Enterprise License Q2-2026</p>
            </div>
            <DollarSign class="size-4 text-muted-foreground" />
          </div>
          
          <div class="flex items-center gap-4 p-3 rounded-lg border">
            <Badge variant="outline" class="w-12 justify-center">22d</Badge>
            <div class="flex-1">
              <p class="text-sm font-medium">Service Level Review Meeting</p>
              <p class="text-xs text-muted-foreground">Infrastructure SLA 2025</p>
            </div>
            <Calendar class="size-4 text-muted-foreground" />
          </div>
          
          <div class="flex items-center gap-4 p-3 rounded-lg border">
            <Badge variant="outline" class="w-12 justify-center">29d</Badge>
            <div class="flex-1">
              <p class="text-sm font-medium">IP Assignment Clause Expiry</p>
              <p class="text-xs text-muted-foreground">R&D Partnership Agreement</p>
            </div>
            <FileText class="size-4 text-muted-foreground" />
          </div>
        </div>
      </CardContent>
    </Card>
    
    <!-- Recently Audited Documents -->
    <Card>
      <CardHeader>
        <div class="flex items-center justify-between">
          <div>
            <CardTitle>Recently Audited Documents</CardTitle>
          </div>
          <Button variant="ghost" size="sm">View all →</Button>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File Name</TableHead>
              <TableHead>Inferred Type</TableHead>
              <TableHead>Critical Risks Found</TableHead>
              <TableHead>Date Processed</TableHead>
              <TableHead>Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell>
                <div class="flex items-center gap-2">
                  <FileText class="size-4 text-muted-foreground" />
                  <span class="text-sm">Enterprise_SaaS_MSA_Q2.pdf</span>
                </div>
              </TableCell>
              <TableCell><Badge variant="secondary">MSA</Badge></TableCell>
              <TableCell><Badge variant="destructive">4 found</Badge></TableCell>
              <TableCell class="text-sm text-muted-foreground">Jun 2, 2026</TableCell>
              <TableCell>
                <Button variant="outline" size="sm">Open Review Pipeline</Button>
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>
                <div class="flex items-center gap-2">
                  <FileText class="size-4 text-muted-foreground" />
                  <span class="text-sm">Vendor_NDA_TechPartners.pdf</span>
                </div>
              </TableCell>
              <TableCell><Badge variant="secondary">NDA</Badge></TableCell>
              <TableCell><Badge variant="destructive">1 found</Badge></TableCell>
              <TableCell class="text-sm text-muted-foreground">Jun 1, 2026</TableCell>
              <TableCell>
                <Button variant="outline" size="sm">Open Review Pipeline</Button>
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>
                <div class="flex items-center gap-2">
                  <FileText class="size-4 text-muted-foreground" />
                  <span class="text-sm">SOW_ProjectBeta_Buildout.docx</span>
                </div>
              </TableCell>
              <TableCell><Badge variant="secondary">SOW</Badge></TableCell>
              <TableCell><Badge variant="destructive">2 found</Badge></TableCell>
              <TableCell class="text-sm text-muted-foreground">May 31, 2026</TableCell>
              <TableCell>
                <Button variant="outline" size="sm">Open Review Pipeline</Button>
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>
                <div class="flex items-center gap-2">
                  <FileText class="size-4 text-muted-foreground" />
                  <span class="text-sm">Infrastructure_SLA_2025.pdf</span>
                </div>
              </TableCell>
              <TableCell><Badge variant="secondary">SLA</Badge></TableCell>
              <TableCell><Badge variant="destructive">6 found</Badge></TableCell>
              <TableCell class="text-sm text-muted-foreground">May 30, 2026</TableCell>
              <TableCell>
                <Button variant="outline" size="sm">Open Review Pipeline</Button>
              </TableCell>
            </TableRow>
            <TableRow>
              <TableCell>
                <div class="flex items-center gap-2">
                  <FileText class="size-4 text-muted-foreground" />
                  <span class="text-sm">R_D_Partnership_Agreement.pdf</span>
                </div>
              </TableCell>
              <TableCell><Badge variant="secondary">MSA</Badge></TableCell>
              <TableCell><Badge variant="destructive">3 found</Badge></TableCell>
              <TableCell class="text-sm text-muted-foreground">May 29, 2026</TableCell>
              <TableCell>
                <Button variant="outline" size="sm">Open Review Pipeline</Button>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>
</template>

<script setup lang="ts">
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FileText, AlertTriangle, Bell, Zap, Clock, DollarSign, Calendar } from '@lucide/vue'
</script>