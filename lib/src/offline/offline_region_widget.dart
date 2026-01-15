import 'dart:async';

import 'package:flutter/material.dart';

import 'offline_manager.dart';

/// Widget for displaying and managing an offline region.
///
/// Shows download progress, status, and provides controls for
/// downloading, pausing, resuming, and deleting regions.
///
/// ## Usage
///
/// ```dart
/// OfflineRegionCard(
///   region: myRegion,
///   onDownload: () => offlineManager.downloadRegion(myRegion),
///   onDelete: () => offlineManager.deleteRegion(myRegion.id),
/// )
/// ```
class OfflineRegionCard extends StatefulWidget {
  /// The offline region to display.
  final OfflineRegion region;

  /// Called when download is requested.
  final VoidCallback? onDownload;

  /// Called when delete is requested.
  final VoidCallback? onDelete;

  /// Called when pause is requested.
  final VoidCallback? onPause;

  /// Called when resume is requested.
  final VoidCallback? onResume;

  /// Whether to show the delete button.
  final bool showDeleteButton;

  const OfflineRegionCard({
    super.key,
    required this.region,
    this.onDownload,
    this.onDelete,
    this.onPause,
    this.onResume,
    this.showDeleteButton = true,
  });

  @override
  State<OfflineRegionCard> createState() => _OfflineRegionCardState();
}

class _OfflineRegionCardState extends State<OfflineRegionCard> {
  StreamSubscription<OfflineRegion>? _subscription;

  @override
  void initState() {
    super.initState();
    _subscription = OfflineManager.instance.regionStatusChanges
        .where((r) => r.id == widget.region.id)
        .listen((_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final region = widget.region;
    final theme = Theme.of(context);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header row
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        region.name,
                        style: theme.textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _getStatusText(region),
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: _getStatusColor(region.status),
                        ),
                      ),
                    ],
                  ),
                ),
                _buildStatusIcon(region.status),
              ],
            ),

            const SizedBox(height: 12),

            // Info chips
            Wrap(
              spacing: 8,
              runSpacing: 4,
              children: [
                _buildInfoChip(
                  Icons.map_outlined,
                  'Zoom ${region.minZoom}-${region.maxZoom}',
                ),
                _buildInfoChip(
                  Icons.layers_outlined,
                  '${region.layers.length} layers',
                ),
                _buildInfoChip(
                  Icons.location_on_outlined,
                  region.stateCode.toUpperCase(),
                ),
                _buildInfoChip(
                  Icons.storage_outlined,
                  _formatBytes(region.status == OfflineRegionStatus.complete
                      ? region.downloadedBytes
                      : region.estimatedBytes),
                ),
              ],
            ),

            // Progress bar (only when downloading)
            if (region.status == OfflineRegionStatus.downloading) ...[
              const SizedBox(height: 16),
              LinearProgressIndicator(
                value: region.progress,
                backgroundColor: theme.colorScheme.surfaceContainerHighest,
              ),
              const SizedBox(height: 8),
              Text(
                '${(region.progress * 100).toStringAsFixed(1)}% - ${_formatBytes(region.downloadedBytes)} / ${_formatBytes(region.estimatedBytes)}',
                style: theme.textTheme.bodySmall,
              ),
            ],

            // Error message
            if (region.status == OfflineRegionStatus.failed && region.errorMessage != null) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: theme.colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(
                      Icons.error_outline,
                      size: 16,
                      color: theme.colorScheme.error,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        region.errorMessage!,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: theme.colorScheme.error,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],

            const SizedBox(height: 16),

            // Action buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                if (widget.showDeleteButton &&
                    region.status != OfflineRegionStatus.downloading)
                  TextButton.icon(
                    onPressed: widget.onDelete,
                    icon: const Icon(Icons.delete_outline, size: 18),
                    label: const Text('Delete'),
                    style: TextButton.styleFrom(
                      foregroundColor: theme.colorScheme.error,
                    ),
                  ),
                const SizedBox(width: 8),
                _buildActionButton(region),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14),
          const SizedBox(width: 4),
          Text(label, style: const TextStyle(fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildStatusIcon(OfflineRegionStatus status) {
    switch (status) {
      case OfflineRegionStatus.complete:
        return Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.green.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.check_circle, color: Colors.green),
        );
      case OfflineRegionStatus.downloading:
        return Container(
          padding: const EdgeInsets.all(8),
          child: const SizedBox(
            width: 24,
            height: 24,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        );
      case OfflineRegionStatus.paused:
        return Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.orange.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.pause_circle, color: Colors.orange),
        );
      case OfflineRegionStatus.failed:
        return Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.red.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.error, color: Colors.red),
        );
      case OfflineRegionStatus.notDownloaded:
        return Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.grey.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: const Icon(Icons.cloud_download_outlined, color: Colors.grey),
        );
    }
  }

  Widget _buildActionButton(OfflineRegion region) {
    switch (region.status) {
      case OfflineRegionStatus.notDownloaded:
      case OfflineRegionStatus.failed:
        return FilledButton.icon(
          onPressed: widget.onDownload,
          icon: const Icon(Icons.download, size: 18),
          label: const Text('Download'),
        );
      case OfflineRegionStatus.downloading:
        return OutlinedButton.icon(
          onPressed: widget.onPause,
          icon: const Icon(Icons.pause, size: 18),
          label: const Text('Pause'),
        );
      case OfflineRegionStatus.paused:
        return FilledButton.icon(
          onPressed: widget.onResume,
          icon: const Icon(Icons.play_arrow, size: 18),
          label: const Text('Resume'),
        );
      case OfflineRegionStatus.complete:
        return OutlinedButton.icon(
          onPressed: null,
          icon: const Icon(Icons.check, size: 18),
          label: const Text('Ready'),
        );
    }
  }

  String _getStatusText(OfflineRegion region) {
    switch (region.status) {
      case OfflineRegionStatus.notDownloaded:
        return 'Not downloaded - tap to save for offline use';
      case OfflineRegionStatus.downloading:
        return 'Downloading...';
      case OfflineRegionStatus.paused:
        return 'Download paused';
      case OfflineRegionStatus.complete:
        if (region.completedAt != null) {
          return 'Downloaded ${_formatDate(region.completedAt!)}';
        }
        return 'Available offline';
      case OfflineRegionStatus.failed:
        return 'Download failed';
    }
  }

  Color _getStatusColor(OfflineRegionStatus status) {
    switch (status) {
      case OfflineRegionStatus.complete:
        return Colors.green;
      case OfflineRegionStatus.downloading:
        return Colors.blue;
      case OfflineRegionStatus.paused:
        return Colors.orange;
      case OfflineRegionStatus.failed:
        return Colors.red;
      case OfflineRegionStatus.notDownloaded:
        return Colors.grey;
    }
  }

  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inDays == 0) {
      return 'today';
    } else if (diff.inDays == 1) {
      return 'yesterday';
    } else if (diff.inDays < 7) {
      return '${diff.inDays} days ago';
    } else {
      return '${date.month}/${date.day}/${date.year}';
    }
  }
}

/// A screen for managing all offline regions.
///
/// Provides a list of regions with download/delete controls
/// and overall cache management.
class OfflineRegionsScreen extends StatefulWidget {
  /// Title for the app bar.
  final String title;

  /// Callback to create a new region.
  final VoidCallback? onCreateRegion;

  const OfflineRegionsScreen({
    super.key,
    this.title = 'Offline Maps',
    this.onCreateRegion,
  });

  @override
  State<OfflineRegionsScreen> createState() => _OfflineRegionsScreenState();
}

class _OfflineRegionsScreenState extends State<OfflineRegionsScreen> {
  final _offlineManager = OfflineManager.instance;
  int _cacheSize = 0;
  StreamSubscription<OfflineRegion>? _subscription;

  @override
  void initState() {
    super.initState();
    _loadCacheSize();
    _subscription = _offlineManager.regionStatusChanges.listen((_) {
      if (mounted) {
        setState(() {});
        _loadCacheSize();
      }
    });
  }

  @override
  void dispose() {
    _subscription?.cancel();
    super.dispose();
  }

  Future<void> _loadCacheSize() async {
    final size = await _offlineManager.getCacheSize();
    if (mounted) {
      setState(() => _cacheSize = size);
    }
  }

  @override
  Widget build(BuildContext context) {
    final regions = _offlineManager.regions;
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
        actions: [
          if (regions.isNotEmpty)
            PopupMenuButton<String>(
              onSelected: (value) {
                if (value == 'clear') {
                  _showClearCacheDialog();
                }
              },
              itemBuilder: (context) => [
                const PopupMenuItem(
                  value: 'clear',
                  child: Row(
                    children: [
                      Icon(Icons.delete_sweep),
                      SizedBox(width: 8),
                      Text('Clear All Cache'),
                    ],
                  ),
                ),
              ],
            ),
        ],
      ),
      body: regions.isEmpty
          ? _buildEmptyState(theme)
          : _buildRegionsList(regions, theme),
      floatingActionButton: widget.onCreateRegion != null
          ? FloatingActionButton.extended(
              onPressed: widget.onCreateRegion,
              icon: const Icon(Icons.add),
              label: const Text('New Region'),
            )
          : null,
    );
  }

  Widget _buildEmptyState(ThemeData theme) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.cloud_off,
              size: 64,
              color: theme.colorScheme.outline,
            ),
            const SizedBox(height: 16),
            Text(
              'No Offline Regions',
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              'Download map regions to use them when you don\'t have cell service.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.outline,
              ),
            ),
            if (widget.onCreateRegion != null) ...[
              const SizedBox(height: 24),
              FilledButton.icon(
                onPressed: widget.onCreateRegion,
                icon: const Icon(Icons.add),
                label: const Text('Create Region'),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildRegionsList(List<OfflineRegion> regions, ThemeData theme) {
    return Column(
      children: [
        // Cache size header
        Container(
          padding: const EdgeInsets.all(16),
          color: theme.colorScheme.surfaceContainerHighest,
          child: Row(
            children: [
              Icon(
                Icons.storage,
                size: 20,
                color: theme.colorScheme.outline,
              ),
              const SizedBox(width: 8),
              Text(
                'Cache: ${_formatBytes(_cacheSize)}',
                style: theme.textTheme.bodyMedium,
              ),
              const Spacer(),
              Text(
                '${regions.length} region${regions.length == 1 ? "" : "s"}',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: theme.colorScheme.outline,
                ),
              ),
            ],
          ),
        ),
        // Regions list
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(vertical: 8),
            itemCount: regions.length,
            itemBuilder: (context, index) {
              final region = regions[index];
              return OfflineRegionCard(
                region: region,
                onDownload: () => _downloadRegion(region),
                onPause: () => _offlineManager.pauseDownload(region.id),
                onResume: () => _resumeDownload(region),
                onDelete: () => _showDeleteDialog(region),
              );
            },
          ),
        ),
      ],
    );
  }

  Future<void> _downloadRegion(OfflineRegion region) async {
    await _offlineManager.downloadRegion(
      region,
      onProgress: (r, progress) {
        if (mounted) setState(() {});
      },
    );
  }

  Future<void> _resumeDownload(OfflineRegion region) async {
    await _offlineManager.resumeDownload(
      region.id,
      onProgress: (r, progress) {
        if (mounted) setState(() {});
      },
    );
  }

  Future<void> _showDeleteDialog(OfflineRegion region) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Region?'),
        content: Text(
          'Are you sure you want to delete "${region.name}"? '
          'You will need to download it again to use it offline.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.error,
            ),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _offlineManager.deleteRegion(region.id);
      if (mounted) setState(() {});
    }
  }

  Future<void> _showClearCacheDialog() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear All Cache?'),
        content: const Text(
          'This will delete all downloaded regions. '
          'You will need to download them again to use them offline.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(
              foregroundColor: Theme.of(context).colorScheme.error,
            ),
            child: const Text('Clear All'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      await _offlineManager.clearCache();
      if (mounted) {
        setState(() {});
        _loadCacheSize();
      }
    }
  }

  String _formatBytes(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    if (bytes < 1024 * 1024 * 1024) {
      return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
    }
    return '${(bytes / (1024 * 1024 * 1024)).toStringAsFixed(1)} GB';
  }
}
