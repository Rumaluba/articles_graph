// Основные переменные
let svg, g, simulation, zoom;
let width, height;
let transform = d3.zoomIdentity;
let currentAbstractLength = 2000;
let currentGraphData = null;
let linkTypes = {
    authors: true,
    keywords: false,
    citations: true
};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM loaded, initializing...");
    initVisualization();
    setupEventListeners();
    loadInitialData();
});

function initVisualization() {
    const container = document.getElementById('graph-container');
    if (!container) {
        console.error("graph-container not found!");
        return;
    }
    
    width = container.clientWidth;
    height = Math.max(600, window.innerHeight - 300);

    d3.select("#graph-container").selectAll("*").remove();

    svg = d3.select("#graph-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .style("background", "#f8f9fa")
        .style("border-radius", "10px")
        .style("cursor", "grab");

    g = svg.append("g");

    zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on("start", function() {
            svg.style("cursor", "grabbing");
        })
        .on("zoom", (event) => {
            transform = event.transform;
            g.attr("transform", transform);
        })
        .on("end", function() {
            svg.style("cursor", "grab");
        });

    svg.call(zoom);

    updateStatus("Visualization ready - waiting for data...");
}

function setupEventListeners() {
    console.log("Setting up event listeners...");
    
    // Основные элементы управления
    const updateGraphBtn = document.getElementById('update-graph');
    const updateArticlesBtn = document.getElementById('update-articles');
    const topicFilter = document.getElementById('topic-filter');
    const startDate = document.getElementById('start-date');
    const endDate = document.getElementById('end-date');
    
    if (updateGraphBtn) updateGraphBtn.addEventListener('click', updateGraph);
    if (updateArticlesBtn) updateArticlesBtn.addEventListener('click', updateArticlesData);
    if (topicFilter) topicFilter.addEventListener('change', updateGraph);
    if (startDate) startDate.addEventListener('change', updateGraph);
    if (endDate) endDate.addEventListener('change', updateGraph);
    
    // Галочки для типов связей
    const authorLinksCheckbox = document.getElementById('show-author-links');
    const keywordLinksCheckbox = document.getElementById('show-keyword-links');
    const citationLinksCheckbox = document.getElementById('show-citation-links');
    
    if (authorLinksCheckbox) {
        authorLinksCheckbox.addEventListener('change', function() {
            linkTypes.authors = this.checked;
            if (currentGraphData) {
                renderGraph(currentGraphData);
            }
        });
    }
    
    if (keywordLinksCheckbox) {
        keywordLinksCheckbox.addEventListener('change', function() {
            linkTypes.keywords = this.checked;
            if (currentGraphData) {
                renderGraph(currentGraphData);
            }
        });
    }
    
    if (citationLinksCheckbox) {
        citationLinksCheckbox.addEventListener('change', function() {
            linkTypes.citations = this.checked;
            if (currentGraphData) {
                renderGraph(currentGraphData);
            }
        });
    }
    
    console.log("Event listeners setup complete");
    
    // Закрытие тултипа по клику вне его
    document.addEventListener('click', function(event) {
        const tooltip = document.getElementById("tooltip");
        if (tooltip && tooltip.style.display === "block" && !tooltip.contains(event.target)) {
            hideTooltip();
        }
    });
}

function updateAbstractDisplay() {
    const tooltip = document.getElementById("tooltip");
    if (!tooltip || tooltip.style.display !== "block") return;
    
    const abstractContent = tooltip.querySelector('.abstract-content');
    if (!abstractContent) return;
    
    const fullAbstract = abstractContent.getAttribute('data-full-abstract');
    
    if (!fullAbstract) return;
    
    if (currentAbstractLength < 2000 && fullAbstract.length > currentAbstractLength) {
        abstractContent.textContent = fullAbstract.substring(0, currentAbstractLength) + '...';
    } else {
        abstractContent.textContent = fullAbstract;
    }
}

function handleResize() {
    const container = document.getElementById('graph-container');
    if (!container) return;
    
    width = container.clientWidth;
    height = Math.max(600, window.innerHeight - 300);
    
    svg.attr("width", width).attr("height", height);
    
    if (simulation) {
        simulation.force("center", d3.forceCenter(width / 2, height / 2));
        simulation.alpha(0.3).restart();
    }
}

function loadInitialData() {
    updateStatus("Loading articles...");
    
    // Устанавливаем даты по умолчанию - последние 2 года
    const endDate = new Date();
    const startDate = new Date();
    startDate.setFullYear(startDate.getFullYear() - 2);
    
    const startDateElem = document.getElementById('start-date');
    const endDateElem = document.getElementById('end-date');
    if (startDateElem) startDateElem.value = startDate.toISOString().split('T')[0];
    if (endDateElem) endDateElem.value = endDate.toISOString().split('T')[0];
    
    updateGraph();
}

function updateGraph() {
    console.log("Update Graph button clicked");
    const topicFilter = document.getElementById('topic-filter');
    const startDateElem = document.getElementById('start-date');
    const endDateElem = document.getElementById('end-date');
    
    if (!topicFilter || !startDateElem || !endDateElem) {
        console.error("Required filter elements not found");
        return;
    }
    
    const topic = topicFilter.value;
    const startDate = startDateElem.value;
    const endDate = endDateElem.value;

    updateStatus("Loading graph data...");

    fetch(`/api/articles?topic=${topic}&start_date=${startDate}&end_date=${endDate}`)
        .then(response => {
            if (!response.ok) throw new Error('Network error');
            return response.json();
        })
        .then(data => {
            console.log("Graph data received:", data.nodes.length, "nodes");
            console.log("Links received:", data.links.length, "links");
            
            if (data.nodes.length === 0) {
                updateStatus("No articles found with current filters");
                g.selectAll("*").remove();
                g.append("text")
                    .attr("x", width / 2)
                    .attr("y", height / 2)
                    .attr("text-anchor", "middle")
                    .style("font-size", "18px")
                    .style("fill", "#666")
                    .text("No articles found. Try updating articles or changing filters.");
                return;
            }
            
            currentGraphData = data;
            renderGraph(data);
            updateStatus(`Displaying ${data.nodes.length} articles with ${data.links.length} connections`);
        })
        .catch(error => {
            console.error('Error:', error);
            updateStatus("Error loading data: " + error.message);
        });
}

function updateArticlesData() {
    console.log("Update Articles button clicked");
    
    const startDateElem = document.getElementById('start-date');
    const endDateElem = document.getElementById('end-date');
    
    if (!startDateElem || !endDateElem) {
        updateStatus("Error: Date range not set");
        return;
    }
    
    const startDate = startDateElem.value;
    const endDate = endDateElem.value;
    
    if (!startDate || !endDate) {
        updateStatus("Please set both start and end dates");
        return;
    }
    
    updateStatus(`Updating articles from ${startDate} to ${endDate}...`);
    
    fetch(`/api/update-articles?start_date=${startDate}&end_date=${endDate}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Update response:", data);
            if (data.status === 'success') {
                updateStatus(data.message + ". Updating graph...");
                setTimeout(() => {
                    updateGraph();
                }, 3000);
            } else {
                updateStatus('Error: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error updating articles:', error);
            updateStatus('Error updating articles: ' + error.message);
        });
}

function calculateNodeSize(citationCount) {
    const minSize = 8;
    const maxSize = 30;
    const scale = Math.log10(Math.max(citationCount, 1) + 1);
    return minSize + (scale * 6);
}

function renderGraph(graphData) {
    g.selectAll("*").remove();

    // Фильтруем связи по выбранным типам
    const filteredLinks = graphData.links.filter(link => {
        if (link.type === 'authors' && linkTypes.authors) return true;
        if (link.type === 'keywords' && linkTypes.keywords) return true;
        if ((link.type === 'cites' || link.type === 'cited_by') && linkTypes.citations) return true;
        return false;
    });

    console.log(`Displaying ${filteredLinks.length} links (authors: ${linkTypes.authors}, keywords: ${linkTypes.keywords}, citations: ${linkTypes.citations})`);

    simulation = d3.forceSimulation(graphData.nodes)
        .force("link", d3.forceLink(filteredLinks).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-30))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(d => calculateNodeSize(d.citation_count || 0) + 8));

    // Рисуем связи
    const link = g.append("g")
        .attr("class", "links")
        .selectAll("line")
        .data(filteredLinks)
        .enter().append("line")
        .attr("stroke", d => {
            if (d.type === 'authors') return '#e74c3c';
            if (d.type === 'cites' || d.type === 'cited_by') return '#f39c12';
            return '#3498db';
        })
        .attr("stroke-opacity", 0.8)
        .attr("stroke-width", d => Math.max(d.strength || 1, 1.5))
        .attr("stroke-dasharray", d => d.type === 'cites' ? "5,5" : "0")
        .on("mouseover", function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr("stroke-width", Math.max(d.strength || 1, 1.5) * 2)
                .attr("stroke-opacity", 1);
        })
        .on("mouseout", function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr("stroke-width", Math.max(d.strength || 1, 1.5))
                .attr("stroke-opacity", 0.8);
        });

    // Рисуем узлы
    const node = g.append("g")
        .attr("class", "nodes")
        .selectAll("circle")
        .data(graphData.nodes)
        .enter().append("circle")
        .attr("r", d => calculateNodeSize(d.citation_count || 0))
        .attr("fill", d => colorByYear(d.year || new Date().getFullYear()))
        .attr("stroke", "#2c3e50")
        .attr("stroke-width", 2)
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr("stroke-width", 4)
                .attr("r", calculateNodeSize(d.citation_count || 0) + 3);
        })
        .on("mouseout", function(event, d) {
            d3.select(this)
                .transition()
                .duration(200)
                .attr("stroke-width", 2)
                .attr("r", calculateNodeSize(d.citation_count || 0));
        })
        .on("click", function(event, d) {
            console.log("Node clicked:", d);
            event.stopPropagation();
            showTooltip(event, d);
        });

    // Добавляем подписи
    const label = g.append("g")
        .attr("class", "labels")
        .selectAll("text")
        .data(graphData.nodes)
        .enter().append("text")
        .text(d => {
            const title = d.title || 'No title';
            const shortTitle = title.length > 20 ? title.substring(0, 20) + "..." : title;
            
            const authors = Array.isArray(d.authors) ? d.authors : [];
            let authorText = '';
            if (authors.length > 0) {
                const firstAuthor = authors[0];
                const lastName = firstAuthor.split(' ').pop();
                authorText = ` (${lastName})`;
            }
            
            return shortTitle + authorText;
        })
        .attr("font-size", 9)
        .attr("dx", 15)
        .attr("dy", 4)
        .style("font-weight", "bold")
        .style("fill", "#34495e")
        .style("text-shadow", "1px 1px 2px white")
        .style("pointer-events", "none");

    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

        label
            .attr("x", d => d.x)
            .attr("y", d => d.y);
    });

    // Добавляем легенду
    addLegend();

    setTimeout(() => {
        svg.transition().duration(750).call(
            zoom.transform,
            d3.zoomIdentity
        );
    }, 1000);
}

function addLegend() {
    const legend = g.append("g")
        .attr("class", "legend")
        .attr("transform", `translate(20, 20)`);

    const legendItems = [];
    
    if (linkTypes.authors) {
        legendItems.push({ color: "#e74c3c", text: "Common authors" });
    }
    if (linkTypes.citations) {
        legendItems.push({ color: "#f39c12", text: "Citations" });
    }
    if (linkTypes.keywords) {
        legendItems.push({ color: "#3498db", text: "Common keywords" });
    }

    legendItems.forEach((item, i) => {
        const legendItem = legend.append("g")
            .attr("transform", `translate(0, ${i * 20})`);

        legendItem.append("line")
            .attr("x1", 0)
            .attr("y1", 0)
            .attr("x2", 20)
            .attr("y2", 0)
            .attr("stroke", item.color)
            .attr("stroke-width", 2)
            .attr("stroke-dasharray", item.text === "Citations" ? "5,5" : "0");

        legendItem.append("text")
            .attr("x", 25)
            .attr("y", 0)
            .attr("dy", "0.3em")
            .style("font-size", "10px")
            .style("fill", "#2c3e50")
            .text(item.text);
    });
}

function showTooltip(event, d) {
    console.log("showTooltip called for:", d);
    const tooltip = document.getElementById("tooltip");
    
    if (!tooltip) {
        console.error("Tooltip element not found!");
        return;
    }
    
    const title = d.title || 'No title';
    const journal = d.journal || 'Unknown';
    const year = d.year || 'Unknown';
    const citationCount = d.citation_count || 0;
    const source = d.source || 'Unknown';
    const url = d.url || '';
    
    const authors = Array.isArray(d.authors) && d.authors.length > 0 ? 
        d.authors.join(', ') : 
        'Authors not available';
    
    const searchKeywords = Array.isArray(d.search_keywords) ? d.search_keywords : [];
    const additionalKeywords = Array.isArray(d.keywords) ? d.keywords : [];
    const allKeywords = [...new Set([...searchKeywords, ...additionalKeywords])];
    
    const abstract = d.full_abstract || d.abstract || 'No abstract available';
    
    tooltip.innerHTML = `
        <div class="tooltip-header">
            <h3>${title}</h3>
            <button class="close-tooltip" onclick="hideTooltip()">×</button>
        </div>
        <div class="meta">
            <strong>Journal:</strong> ${journal} | 
            <strong>Year:</strong> ${year} | 
            <strong>Citations:</strong> ${citationCount}<br>
            <strong>Authors:</strong> ${authors}<br>
            <strong>Source:</strong> ${source}
        </div>
        <div class="url-section">
            <strong>URL:</strong> 
            ${url ? `<a href="${url}" target="_blank" class="article-link">${url}</a>` : 'Not available'}
        </div>
        <div class="abstract-controls">
            <label for="abstract-slider">Abstract length:</label>
            <input type="range" id="abstract-slider" min="100" max="2000" value="2000" step="100">
            <span id="abstract-length">Full</span>
        </div>
        <div class="abstract-section">
            <strong>Abstract:</strong> 
            <div class="abstract-content" data-full-abstract="${abstract.replace(/"/g, '&quot;')}">
                ${abstract}
            </div>
        </div>
        <div class="keywords">
            <strong>Keywords:</strong> ${allKeywords.length > 0 ? allKeywords.join(', ') : 'No keywords available'}
        </div>
    `;
    
    tooltip.style.display = 'block';
    tooltip.style.opacity = '1';
    
    const abstractSlider = document.getElementById('abstract-slider');
    if (abstractSlider) {
        abstractSlider.addEventListener('input', function() {
            currentAbstractLength = parseInt(this.value);
            const lengthDisplay = document.getElementById('abstract-length');
            if (lengthDisplay) {
                lengthDisplay.textContent = currentAbstractLength === 2000 ? 'Full' : currentAbstractLength + ' chars';
            }
            updateAbstractDisplay();
        });
    }
    
    positionTooltip(event, tooltip);
}

function positionTooltip(event, tooltip) {
    const tooltipRect = tooltip.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    let left = event.pageX + 15;
    let top = event.pageY - 15;
    
    if (left + tooltipRect.width > viewportWidth - 20) {
        left = viewportWidth - tooltipRect.width - 20;
    }
    
    if (top + tooltipRect.height > viewportHeight - 20) {
        top = viewportHeight - tooltipRect.height - 20;
    }
    
    if (left < 20) {
        left = 20;
    }
    
    if (top < 20) {
        top = 20;
    }
    
    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById("tooltip");
    if (tooltip) {
        tooltip.style.opacity = '0';
        tooltip.style.display = 'none';
    }
}

function colorByYear(year) {
    const currentYear = new Date().getFullYear();
    const age = currentYear - year;
    
    if (age > 20) return "#2c3e50";
    if (age > 10) return "#3498db";
    if (age > 5) return "#f39c12";
    if (age > 2) return "#e74c3c";
    return "#c0392b";
}

function updateStatus(message) {
    const status = document.getElementById('status');
    if (status) {
        status.textContent = message;
    }
}

// Делаем функции глобальными для обработчиков onclick в HTML
window.hideTooltip = hideTooltip;
window.updateGraph = updateGraph;
window.updateArticlesData = updateArticlesData;
window.updateAbstractDisplay = updateAbstractDisplay;

// Добавляем обработчик resize
window.addEventListener('resize', handleResize);
