// VectorBid Data Flow Visualization
// Interactive SVG-based diagram showing system architecture

class DataFlowVisualization {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.svg = null;
        this.width = 1200;
        this.height = 800;
        this.animationSpeed = 1000;
        this.isAnimating = false;
        
        this.nodes = [
            // Input Layer
            { id: 'pilot', x: 100, y: 150, width: 120, height: 60, label: 'Pilot\nPreferences', type: 'input', color: '#00d4ff' },
            { id: 'context', x: 100, y: 250, width: 120, height: 60, label: 'Context\nData', type: 'input', color: '#00d4ff' },
            { id: 'rules', x: 100, y: 350, width: 120, height: 60, label: 'Rule\nPacks', type: 'input', color: '#00d4ff' },
            
            // Processing Layer
            { id: 'parser', x: 350, y: 100, width: 140, height: 60, label: 'NLP Parser\n(GPT-4)', type: 'process', color: '#39ff14' },
            { id: 'validator', x: 350, y: 200, width: 140, height: 60, label: 'Rules\nValidator', type: 'process', color: '#39ff14' },
            { id: 'optimizer', x: 350, y: 300, width: 140, height: 60, label: 'AI\nOptimizer', type: 'process', color: '#39ff14' },
            { id: 'fusion', x: 350, y: 400, width: 140, height: 60, label: 'Data\nFusion', type: 'process', color: '#39ff14' },
            
            // Analysis Layer
            { id: 'analyzer', x: 600, y: 150, width: 140, height: 60, label: 'Route\nAnalyzer', type: 'analysis', color: '#ff6b35' },
            { id: 'scorer', x: 600, y: 250, width: 140, height: 60, label: 'Schedule\nScorer', type: 'analysis', color: '#ff6b35' },
            { id: 'strategy', x: 600, y: 350, width: 140, height: 60, label: 'Strategy\nEngine', type: 'analysis', color: '#ff6b35' },
            
            // Output Layer
            { id: 'candidates', x: 850, y: 150, width: 140, height: 60, label: 'Schedule\nCandidates', type: 'output', color: '#bf00ff' },
            { id: 'export', x: 850, y: 250, width: 140, height: 60, label: 'PBS\nExport', type: 'output', color: '#bf00ff' },
            { id: 'insights', x: 850, y: 350, width: 140, height: 60, label: 'AI\nInsights', type: 'output', color: '#bf00ff' },
            
            // External Systems
            { id: 'pbs', x: 1050, y: 200, width: 100, height: 60, label: 'PBS\nSystem', type: 'external', color: '#ffd700' },
            { id: 'dashboard', x: 1050, y: 300, width: 100, height: 60, label: 'User\nDashboard', type: 'external', color: '#ffd700' }
        ];
        
        this.connections = [
            // Input to Processing
            { from: 'pilot', to: 'parser', type: 'data', label: 'Natural Language' },
            { from: 'context', to: 'validator', type: 'data', label: 'Profile Data' },
            { from: 'rules', to: 'validator', type: 'data', label: 'Constraints' },
            { from: 'pilot', to: 'optimizer', type: 'data', label: 'Preferences' },
            
            // Processing to Analysis
            { from: 'parser', to: 'analyzer', type: 'processed', label: 'Structured Data' },
            { from: 'validator', to: 'scorer', type: 'processed', label: 'Valid Options' },
            { from: 'optimizer', to: 'strategy', type: 'processed', label: 'Optimization' },
            { from: 'fusion', to: 'analyzer', type: 'processed', label: 'Fused Data' },
            
            // Cross-layer Processing
            { from: 'parser', to: 'fusion', type: 'processed', label: 'Parsed Prefs' },
            { from: 'validator', to: 'fusion', type: 'processed', label: 'Validation' },
            { from: 'optimizer', to: 'fusion', type: 'processed', label: 'Optimization' },
            
            // Analysis to Output
            { from: 'analyzer', to: 'candidates', type: 'analyzed', label: 'Ranked Routes' },
            { from: 'scorer', to: 'candidates', type: 'analyzed', label: 'Scores' },
            { from: 'strategy', to: 'insights', type: 'analyzed', label: 'Strategy' },
            { from: 'candidates', to: 'export', type: 'output', label: 'Schedule Data' },
            
            // Output to External
            { from: 'export', to: 'pbs', type: 'external', label: 'PBS Format' },
            { from: 'insights', to: 'dashboard', type: 'external', label: 'User Interface' },
            { from: 'candidates', to: 'dashboard', type: 'external', label: 'Results' }
        ];
        
        this.init();
    }
    
    init() {
        this.createSVG();
        this.renderNodes();
        this.renderConnections();
        this.addInteractivity();
        this.addLegend();
    }
    
    createSVG() {
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .style('background', 'linear-gradient(135deg, #0a0f1c 0%, #1a1f2e 100%)')
            .style('border-radius', '12px')
            .style('border', '2px solid #00d4ff')
            .style('box-shadow', '0 0 20px rgba(0, 212, 255, 0.3)');
        
        // Add grid pattern
        const defs = this.svg.append('defs');
        const pattern = defs.append('pattern')
            .attr('id', 'grid')
            .attr('width', 50)
            .attr('height', 50)
            .attr('patternUnits', 'userSpaceOnUse');
        
        pattern.append('path')
            .attr('d', 'M 50 0 L 0 0 0 50')
            .attr('fill', 'none')
            .attr('stroke', '#00d4ff')
            .attr('stroke-width', 0.5)
            .attr('opacity', 0.1);
        
        this.svg.append('rect')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('fill', 'url(#grid)');
    }
    
    renderConnections() {
        const connectionGroup = this.svg.append('g').attr('class', 'connections');
        
        this.connections.forEach((conn, index) => {
            const fromNode = this.nodes.find(n => n.id === conn.from);
            const toNode = this.nodes.find(n => n.id === conn.to);
            
            if (!fromNode || !toNode) return;
            
            const startX = fromNode.x + fromNode.width;
            const startY = fromNode.y + fromNode.height / 2;
            const endX = toNode.x;
            const endY = toNode.y + toNode.height / 2;
            
            const midX = (startX + endX) / 2;
            
            // Create curved path
            const path = connectionGroup.append('path')
                .attr('d', `M ${startX} ${startY} Q ${midX} ${startY} ${midX} ${(startY + endY) / 2} Q ${midX} ${endY} ${endX} ${endY}`)
                .attr('fill', 'none')
                .attr('stroke', this.getConnectionColor(conn.type))
                .attr('stroke-width', 2)
                .attr('opacity', 0.6)
                .attr('class', `connection connection-${conn.type}`)
                .style('filter', `drop-shadow(0 0 5px ${this.getConnectionColor(conn.type)})`);
            
            // Add arrowhead
            this.addArrowhead(connectionGroup, endX - 10, endY, this.getConnectionColor(conn.type));
            
            // Add data flow animation
            const circle = connectionGroup.append('circle')
                .attr('r', 4)
                .attr('fill', this.getConnectionColor(conn.type))
                .attr('opacity', 0)
                .style('filter', `drop-shadow(0 0 8px ${this.getConnectionColor(conn.type)})`);
            
            // Animate data flow
            this.animateDataFlow(circle, path.node(), index * 200);
        });
    }
    
    renderNodes() {
        const nodeGroup = this.svg.append('g').attr('class', 'nodes');
        
        this.nodes.forEach(node => {
            const group = nodeGroup.append('g')
                .attr('class', `node node-${node.type}`)
                .attr('transform', `translate(${node.x}, ${node.y})`);
            
            // Node background
            group.append('rect')
                .attr('width', node.width)
                .attr('height', node.height)
                .attr('rx', 8)
                .attr('fill', 'rgba(26, 31, 46, 0.9)')
                .attr('stroke', node.color)
                .attr('stroke-width', 2)
                .style('filter', `drop-shadow(0 0 10px ${node.color})`);
            
            // Node label
            group.append('text')
                .attr('x', node.width / 2)
                .attr('y', node.height / 2)
                .attr('text-anchor', 'middle')
                .attr('dominant-baseline', 'middle')
                .attr('fill', node.color)
                .attr('font-family', 'JetBrains Mono, monospace')
                .attr('font-size', '12px')
                .attr('font-weight', '600')
                .style('text-shadow', `0 0 5px ${node.color}`)
                .selectAll('tspan')
                .data(node.label.split('\\n'))
                .enter()
                .append('tspan')
                .attr('x', node.width / 2)
                .attr('dy', (d, i) => i === 0 ? '-0.3em' : '1.2em')
                .text(d => d);
            
            // Add pulse animation for processing nodes
            if (node.type === 'process') {
                group.select('rect').style('animation', 'pulse 2s infinite');
            }
        });
    }
    
    addArrowhead(container, x, y, color) {
        container.append('polygon')
            .attr('points', `${x},${y} ${x-8},${y-4} ${x-8},${y+4}`)
            .attr('fill', color)
            .style('filter', `drop-shadow(0 0 3px ${color})`);
    }
    
    getConnectionColor(type) {
        const colors = {
            'data': '#00d4ff',
            'processed': '#39ff14',
            'analyzed': '#ff6b35',
            'output': '#bf00ff',
            'external': '#ffd700'
        };
        return colors[type] || '#ffffff';
    }
    
    animateDataFlow(circle, path, delay) {
        const totalLength = path.getTotalLength();
        
        const animate = () => {
            circle.attr('opacity', 0.8)
                .transition()
                .duration(this.animationSpeed)
                .ease(d3.easeLinear)
                .attrTween('transform', () => {
                    return (t) => {
                        const point = path.getPointAtLength(t * totalLength);
                        return `translate(${point.x}, ${point.y})`;
                    };
                })
                .transition()
                .duration(200)
                .attr('opacity', 0)
                .on('end', () => {
                    setTimeout(animate, delay + Math.random() * 2000);
                });
        };
        
        setTimeout(animate, delay);
    }
    
    addInteractivity() {
        // Add hover effects
        this.svg.selectAll('.node')
            .on('mouseover', function(event, d) {
                d3.select(this).select('rect')
                    .transition()
                    .duration(200)
                    .attr('stroke-width', 4)
                    .style('filter', 'drop-shadow(0 0 20px currentColor)');
            })
            .on('mouseout', function(event, d) {
                d3.select(this).select('rect')
                    .transition()
                    .duration(200)
                    .attr('stroke-width', 2)
                    .style('filter', 'drop-shadow(0 0 10px currentColor)');
            });
        
        // Add click to highlight path
        this.svg.selectAll('.node')
            .on('click', (event, d) => {
                this.highlightNodePath(d);
            });
    }
    
    highlightNodePath(nodeData) {
        // Reset all connections
        this.svg.selectAll('.connection')
            .transition()
            .duration(300)
            .attr('opacity', 0.3)
            .attr('stroke-width', 1);
        
        // Highlight relevant connections
        const relevantConnections = this.connections.filter(conn => 
            conn.from === nodeData.id || conn.to === nodeData.id
        );
        
        relevantConnections.forEach(conn => {
            this.svg.select(`.connection-${conn.type}`)
                .transition()
                .duration(300)
                .attr('opacity', 1)
                .attr('stroke-width', 4);
        });
        
        // Reset after 3 seconds
        setTimeout(() => {
            this.svg.selectAll('.connection')
                .transition()
                .duration(500)
                .attr('opacity', 0.6)
                .attr('stroke-width', 2);
        }, 3000);
    }
    
    addLegend() {
        const legend = this.svg.append('g')
            .attr('class', 'legend')
            .attr('transform', 'translate(50, 500)');
        
        const legendData = [
            { type: 'input', color: '#00d4ff', label: 'Input Layer' },
            { type: 'process', color: '#39ff14', label: 'Processing Layer' },
            { type: 'analysis', color: '#ff6b35', label: 'Analysis Layer' },
            { type: 'output', color: '#bf00ff', label: 'Output Layer' },
            { type: 'external', color: '#ffd700', label: 'External Systems' }
        ];
        
        legend.append('text')
            .attr('x', 0)
            .attr('y', 0)
            .attr('fill', '#00d4ff')
            .attr('font-family', 'JetBrains Mono, monospace')
            .attr('font-size', '14px')
            .attr('font-weight', '700')
            .style('text-shadow', '0 0 5px #00d4ff')
            .text('VectorBid AI Data Flow Architecture');
        
        const legendItems = legend.selectAll('.legend-item')
            .data(legendData)
            .enter()
            .append('g')
            .attr('class', 'legend-item')
            .attr('transform', (d, i) => `translate(0, ${30 + i * 25})`);
        
        legendItems.append('rect')
            .attr('width', 15)
            .attr('height', 15)
            .attr('fill', d => d.color)
            .attr('stroke', d => d.color)
            .attr('stroke-width', 1)
            .style('filter', d => `drop-shadow(0 0 3px ${d.color})`);
        
        legendItems.append('text')
            .attr('x', 25)
            .attr('y', 12)
            .attr('fill', d => d.color)
            .attr('font-family', 'JetBrains Mono, monospace')
            .attr('font-size', '12px')
            .style('text-shadow', d => `0 0 3px ${d.color}`)
            .text(d => d.label);
    }
    
    startAnimation() {
        if (this.isAnimating) return;
        this.isAnimating = true;
        
        // Add pulsing animation to processing nodes
        this.svg.selectAll('.node-process rect')
            .style('animation', 'glow 2s infinite alternate');
    }
    
    stopAnimation() {
        this.isAnimating = false;
        
        this.svg.selectAll('.node-process rect')
            .style('animation', 'none');
    }
}

// CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    @keyframes glow {
        0% { filter: drop-shadow(0 0 10px currentColor); }
        100% { filter: drop-shadow(0 0 20px currentColor) drop-shadow(0 0 30px currentColor); }
    }
`;
document.head.appendChild(style);

// Export for use
window.DataFlowVisualization = DataFlowVisualization;