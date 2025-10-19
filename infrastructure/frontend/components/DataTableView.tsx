'use client';

import { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api-client';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { showErrorToast } from '@/lib/toast-utils';
import IncidentDetailModal from './IncidentDetailModal';

interface Incident {
  id: string;
  domain_id: string;
  raw_text: string;
  structured_data: Record<string, any>;
  location?: { latitude: number; longitude: number };
  created_at: string;
  images?: string[];
}

interface DataTableViewProps {
  domainId: string;
}

interface Filters {
  dateRange: string;
  location: string;
  category: string;
}

type SortDirection = 'asc' | 'desc' | null;

export default function DataTableView({ domainId }: DataTableViewProps) {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [columns, setColumns] = useState<string[]>([]);
  const [filters, setFilters] = useState<Filters>({
    dateRange: 'all',
    location: '',
    category: 'all',
  });
  const [categories, setCategories] = useState<string[]>([]);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalIncidents, setTotalIncidents] = useState(0);
  const itemsPerPage = 20;
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchIncidents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [domainId, currentPage]);

  const fetchIncidents = async () => {
    setLoading(true);
    try {
      // Build filters object
      const apiFilters: any = { domain_id: domainId };

      // Add date range filter
      if (filters.dateRange !== 'all') {
        const now = new Date();
        let startDate: Date;

        switch (filters.dateRange) {
          case 'today':
            startDate = new Date(now.setHours(0, 0, 0, 0));
            break;
          case 'week':
            startDate = new Date(now.setDate(now.getDate() - 7));
            break;
          case 'month':
            startDate = new Date(now.setMonth(now.getMonth() - 1));
            break;
          case 'year':
            startDate = new Date(now.setFullYear(now.getFullYear() - 1));
            break;
          default:
            startDate = new Date(0);
        }

        apiFilters.start_date = startDate.toISOString();
      }

      // Add location filter
      if (filters.location.trim()) {
        apiFilters.location = filters.location.trim();
      }

      // Add category filter
      if (filters.category !== 'all') {
        apiFilters.category = filters.category;
      }

      const queryParams = new URLSearchParams({
        type: 'retrieval',
        filters: JSON.stringify(apiFilters),
        page: currentPage.toString(),
        per_page: itemsPerPage.toString(),
      });

      const response = await apiRequest<{ data: Incident[]; pagination?: any }>(
        `/data?${queryParams.toString()}`,
        {},
        false
      );

      if (response.error) {
        // Only show error toast for non-auth errors
        if (response.status !== 401 && response.status !== 403) {
          showErrorToast('Failed to fetch incidents', response.error);
        }
        setIncidents([]);
        return;
      }

      const incidentData = response.data?.data || [];
      setIncidents(incidentData);

      // Update pagination info
      if (response.data?.pagination) {
        setTotalPages(response.data.pagination.total_pages || 1);
        setTotalIncidents(response.data.pagination.total || incidentData.length);
      } else {
        setTotalPages(1);
        setTotalIncidents(incidentData.length);
      }

      // Extract unique columns and categories from structured_data
      if (incidentData.length > 0) {
        const allKeys = new Set<string>();
        const allCategories = new Set<string>();

        incidentData.forEach((incident) => {
          Object.keys(incident.structured_data || {}).forEach((agentName) => {
            const agentData = incident.structured_data[agentName];
            if (typeof agentData === 'object' && agentData !== null) {
              Object.keys(agentData).forEach((key) => {
                allKeys.add(`${agentName}.${key}`);
              });

              // Extract category if available
              if (agentData.category) {
                allCategories.add(String(agentData.category));
              }
            }
          });
        });

        setColumns(Array.from(allKeys));
        setCategories(Array.from(allCategories));
      }
    } catch (error) {
      console.error('Error fetching incidents:', error);
      showErrorToast('Error', 'Failed to load incidents');
      setIncidents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key: keyof Filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    setCurrentPage(1); // Reset to first page when applying filters
    fetchIncidents();
  };

  const clearFilters = () => {
    setFilters({
      dateRange: 'all',
      location: '',
      category: 'all',
    });
    setCurrentPage(1); // Reset to first page
    // Fetch will be triggered by useEffect when filters change
    setTimeout(() => fetchIncidents(), 0);
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const handleRowClick = (incident: Incident) => {
    setSelectedIncident(incident);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedIncident(null);
  };

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      // Toggle sort direction
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortColumn(null);
        setSortDirection(null);
      } else {
        setSortDirection('asc');
      }
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const getSortedIncidents = () => {
    if (!sortColumn || !sortDirection) {
      return incidents;
    }

    return [...incidents].sort((a, b) => {
      let aValue: any;
      let bValue: any;

      if (sortColumn === 'id') {
        aValue = a.id;
        bValue = b.id;
      } else if (sortColumn === 'created_at') {
        aValue = new Date(a.created_at).getTime();
        bValue = new Date(b.created_at).getTime();
      } else if (sortColumn === 'location') {
        aValue = a.location
          ? `${a.location.latitude},${a.location.longitude}`
          : '';
        bValue = b.location
          ? `${b.location.latitude},${b.location.longitude}`
          : '';
      } else {
        // Nested column from structured_data
        aValue = getNestedValue(a.structured_data, sortColumn);
        bValue = getNestedValue(b.structured_data, sortColumn);
      }

      // Handle null/undefined values
      if (aValue === '-' || aValue === null || aValue === undefined) return 1;
      if (bValue === '-' || bValue === null || bValue === undefined) return -1;

      // Compare values
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  };

  const SortIcon = ({ column }: { column: string }) => {
    if (sortColumn !== column) {
      return <span className="ml-1 text-muted-foreground">⇅</span>;
    }
    if (sortDirection === 'asc') {
      return <span className="ml-1">↑</span>;
    }
    if (sortDirection === 'desc') {
      return <span className="ml-1">↓</span>;
    }
    return null;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffHours < 1) {
      const diffMins = Math.floor(diffMs / (1000 * 60));
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getNestedValue = (obj: any, path: string): any => {
    const [agentName, ...keys] = path.split('.');
    const agentData = obj[agentName];
    if (!agentData) return '-';

    let value = agentData;
    for (const key of keys) {
      if (value && typeof value === 'object') {
        value = value[key];
      } else {
        return '-';
      }
    }

    if (value === null || value === undefined) return '-';
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  };

  const formatColumnName = (column: string): string => {
    return column
      .split('.')
      .map((part) => part.replace(/_/g, ' '))
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' - ');
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="text-muted-foreground">Loading incidents...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (incidents.length === 0) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <div className="text-muted-foreground">No incidents found</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Incidents ({incidents.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="mb-4 flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label className="text-sm font-medium mb-2 block">Date Range</label>
            <Select
              value={filters.dateRange}
              onValueChange={(value) => handleFilterChange('dateRange', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select date range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All time</SelectItem>
                <SelectItem value="today">Today</SelectItem>
                <SelectItem value="week">This week</SelectItem>
                <SelectItem value="month">This month</SelectItem>
                <SelectItem value="year">This year</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label className="text-sm font-medium mb-2 block">Location</label>
            <Input
              placeholder="Search location..."
              value={filters.location}
              onChange={(e) => handleFilterChange('location', e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  applyFilters();
                }
              }}
            />
          </div>

          <div className="flex-1 min-w-[200px]">
            <label className="text-sm font-medium mb-2 block">Category</label>
            <Select
              value={filters.category}
              onValueChange={(value) => handleFilterChange('category', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>
                    {cat}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-end gap-2">
            <Button onClick={applyFilters}>Apply Filters</Button>
            <Button variant="outline" onClick={clearFilters}>
              Clear
            </Button>
          </div>
        </div>

        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  className="w-[100px] cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('id')}
                >
                  ID <SortIcon column="id" />
                </TableHead>
                <TableHead
                  className="w-[150px] cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('created_at')}
                >
                  Time <SortIcon column="created_at" />
                </TableHead>
                <TableHead
                  className="w-[200px] cursor-pointer hover:bg-muted/50"
                  onClick={() => handleSort('location')}
                >
                  Location <SortIcon column="location" />
                </TableHead>
                <TableHead className="min-w-[300px]">Report</TableHead>
                {columns.slice(0, 5).map((column) => (
                  <TableHead
                    key={column}
                    className="min-w-[150px] cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort(column)}
                  >
                    {formatColumnName(column)} <SortIcon column={column} />
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {getSortedIncidents().map((incident) => (
                <TableRow
                  key={incident.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => handleRowClick(incident)}
                >
                  <TableCell className="font-mono text-xs">
                    {incident.id.slice(0, 8)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {formatDate(incident.created_at)}
                  </TableCell>
                  <TableCell className="text-sm">
                    {incident.location
                      ? `${incident.location.latitude.toFixed(4)}, ${incident.location.longitude.toFixed(4)}`
                      : '-'}
                  </TableCell>
                  <TableCell className="text-sm">
                    <div className="max-w-[300px] truncate" title={incident.raw_text}>
                      {incident.raw_text}
                    </div>
                  </TableCell>
                  {columns.slice(0, 5).map((column) => (
                    <TableCell key={column} className="text-sm">
                      <div className="max-w-[150px] truncate">
                        {getNestedValue(incident.structured_data, column)}
                      </div>
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              Showing {(currentPage - 1) * itemsPerPage + 1} to{' '}
              {Math.min(currentPage * itemsPerPage, totalIncidents)} of{' '}
              {totalIncidents} incidents
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(1)}
                disabled={currentPage === 1}
              >
                First
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum: number;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }

                  return (
                    <Button
                      key={pageNum}
                      variant={currentPage === pageNum ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => handlePageChange(pageNum)}
                    >
                      {pageNum}
                    </Button>
                  );
                })}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handlePageChange(totalPages)}
                disabled={currentPage === totalPages}
              >
                Last
              </Button>
            </div>
          </div>
        )}
      </CardContent>

      {/* Incident Detail Modal */}
      <IncidentDetailModal
        incident={selectedIncident}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </Card>
  );
}
