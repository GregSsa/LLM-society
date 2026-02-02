import logging
import random
from collections import defaultdict
from .baseEnvironment import BaseEnvironment


class DebateEnvironment(BaseEnvironment):
    """Environment for debate and consensus building with relationships and opinion tracking."""
    
    def __init__(self, description, rules, questions: list = None, relationships: dict = None, debate_deadline: int = 5):
        super().__init__(description, rules)
        self.questions = questions or []
        self.current_question = None
        self.topic = ""
        self.opinions = {}  # agent_id -> opinion_value (-1.0 to 1.0)
        self.opinion_history = {}  # agent_id -> [list of opinion values]
        self.relationships = relationships or {}  # agent_id -> {other_agent_id: relationship_type}
        self.vote_count = 0
        self.votes = {}  # agent_id -> vote (for/against/abstain)
        self.arguments = []  # list of arguments presented
        self.messages_this_step = {}  # agent_id -> count of messages
        self.consensus_threshold = 0.75  # 75% agreement needed
        self.is_consensus = False
        self.final_voting = False
        self.dissenting_agent = None  # agent who still disagrees
        self.dissent_turn_used = False
        self.debate_deadline = debate_deadline  # Force voting after N steps
        self.voting_forced = False
        self.all_agents = []  # Will be populated when agents first act
        
        # Choose a random question if available
        if self.questions:
            self._select_random_question()
        
        logging.info(f"DebateEnvironment initialized with {debate_deadline}-step debate deadline")
    
    def _select_random_question(self):
        """Select a random question and set initial opinions."""
        self.current_question = random.choice(self.questions)
        self.topic = self.current_question['topic']
        logging.info(f"Question selected: {self.topic}")
    
    def set_initial_opinions(self, opinions_dict):
        """Set initial opinions for agents and initialize history."""
        self.opinions = opinions_dict.copy()
        for agent_id, opinion in self.opinions.items():
            self.opinion_history[agent_id] = [opinion]
        logging.info(f"Initial opinions set: {self.opinions}")
    
    def set_relationships(self, relationships_dict):
        """Set relationships between agents.
        relationships_dict: {agent_id: {other_agent_id: relationship_type}}
        """
        self.relationships = relationships_dict
        logging.info("Relationships established")
    
    def print_relationships(self):
        """Print all relationships at the start of simulation."""
        if not self.relationships:
            logging.info("No relationships defined")
            return
        
        logging.info("=" * 60)
        logging.info("AGENT RELATIONSHIPS")
        logging.info("=" * 60)
        for agent_id, relations in sorted(self.relationships.items()):
            if relations:
                for other_id, relation_type in sorted(relations.items()):
                    logging.info(f"{agent_id} -> {other_id}: {relation_type}")
        logging.info("=" * 60)
    
    def perform_action(self, agent, action_details):
        """Process agent actions during debate."""
        if self.is_consensus and not (self.final_voting and self.dissenting_agent == agent.id):
            return
        
        super().perform_action(agent, action_details)
        
        env_action = action_details.get('env_action')
        params = action_details.get('params', {}) or {}
        
        if env_action == 'message':
            target_agent = params.get('target_agent_id')
            message = params.get('message', '')
            self._process_message(agent.id, target_agent, message)
            
        elif env_action == 'change_opinion':
            shift = params.get('shift', 0.0)
            self._update_opinion(agent.id, shift)
            
        elif env_action == 'vote':
            vote = params.get('vote', 'abstain')
            self._record_vote(agent.id, vote)
    
    def _process_message(self, sender_id: str, target_id: str, message: str):
        """Process a message from one agent to another."""
        # Check message limits
        if sender_id not in self.messages_this_step:
            self.messages_this_step[sender_id] = 0
        
        if self.messages_this_step[sender_id] >= 2:
            logging.warning(f"Agent {sender_id} has reached max 2 messages per step")
            return
        
        self.messages_this_step[sender_id] += 1
        
        # Log the message
        message_entry = {
            'from': sender_id,
            'to': target_id,
            'message': message,
            'step': self.step
        }
        self.arguments.append(message_entry)
        
        logging.info(f"[Message] {sender_id} -> {target_id}: {message}")
        
        # Apply message impact with relationship weighting
        self._apply_message_impact(sender_id, target_id, message)
    
    def _apply_message_impact(self, sender_id: str, target_id: str, message: str):
        """Apply opinion shift based on relationship and message quality."""
        # Get relationship weight
        relationship_weight = self._get_relationship_weight(sender_id, target_id)
        
        # Calculate base opinion shift from message length and structure
        # Longer, structured messages have more impact
        message_length = len(message)
        message_quality = min(1.0, message_length / 200.0)  # Normalize to ~200 chars as optimal
        
        # Calculate argument strength indicators
        argument_strength = self._calculate_argument_strength(message)
        
        # Combined impact: relationship * message_quality * argument_strength
        impact_weight = relationship_weight * message_quality * argument_strength
        
        # Apply shift (moderate impact: -0.15 to +0.15 per message)
        base_shift = 0.15 * impact_weight
        
        # Randomize slightly to avoid predictability
        import random
        variance = random.uniform(0.8, 1.2)
        final_shift = base_shift * variance
        
        # Apply the shift
        if target_id in self.opinions:
            self._update_opinion(target_id, final_shift, sender_id)
    
    def _get_relationship_weight(self, sender_id: str, target_id: str) -> float:
        """Get the weight multiplier based on relationship between sender and target.
        Returns a value between 0.5 (distrust) and 1.5 (strong trust).
        """
        if not self.relationships or sender_id not in self.relationships:
            return 1.0  # Neutral weight
        
        relations = self.relationships[sender_id]
        if target_id not in relations:
            return 1.0  # No specific relationship
        
        relationship_type = relations[target_id].lower()
        
        # Define weights based on relationship types
        weights = {
            "respects": 1.3,
            "trusts": 1.4,
            "strong trust": 1.5,
            "agrees": 1.2,
            "admires": 1.3,
            "sympathizes": 1.2,
            "appreciates": 1.2,
            
            "distrusts": 0.6,
            "dislikes": 0.5,
            "skeptical": 0.8,
            "skeptical of": 0.8,
            "challenges": 0.9,
            "opposes": 0.5,
            
            "finds": 1.1,  # "finds passionate", "finds ally"
            "sees": 1.0,   # "sees as ally"
            "ally": 1.3,
        }
        
        # Find best matching weight
        best_weight = 1.0
        for key, weight in weights.items():
            if key in relationship_type:
                best_weight = weight
                break
        
        return best_weight
    
    def _calculate_argument_strength(self, message: str) -> float:
        """Calculate argument strength based on linguistic indicators.
        Returns a value between 0.5 and 1.5.
        """
        strength = 1.0
        
        message_lower = message.lower()
        
        # Strong indicators (increase impact)
        strong_indicators = [
            "research shows", "evidence suggests", "data indicates",
            "studies prove", "statistically", "according to",
            "fact is", "clearly", "obviously", "undeniably",
            "because", "therefore", "thus", "consequently",
            "however", "but", "though", "on the other hand"
        ]
        
        # Weak indicators (decrease impact)
        weak_indicators = [
            "maybe", "perhaps", "might", "could be", "possibly",
            "i think", "i feel", "in my opinion", "seems like",
            "probably", "supposedly", "allegedly", "so-called"
        ]
        
        # Count indicators
        strong_count = sum(1 for indicator in strong_indicators if indicator in message_lower)
        weak_count = sum(1 for indicator in weak_indicators if indicator in message_lower)
        
        # Adjust strength
        strength += strong_count * 0.1
        strength -= weak_count * 0.08
        
        # Passion indicators (adds authenticity)
        if any(word in message_lower for word in ["must", "need", "important", "critical", "urgent"]):
            strength += 0.1
        
        # Questions (show engagement)
        if "?" in message:
            strength += 0.05
        
        # Clamp to reasonable bounds
        strength = max(0.5, min(1.5, strength))
        
        return strength
    
    def _update_opinion(self, agent_id: str, shift: float, source_agent: str = None):
        """Update an agent's opinion and track change."""
        if agent_id not in self.opinions:
            self.opinions[agent_id] = 0.0
        
        # Clamp shift to reasonable bounds
        shift = max(-1.0, min(1.0, shift))
        old_opinion = self.opinions[agent_id]
        self.opinions[agent_id] = max(-1.0, min(1.0, old_opinion + shift))
        
        # Track history
        if agent_id not in self.opinion_history:
            self.opinion_history[agent_id] = []
        self.opinion_history[agent_id].append(self.opinions[agent_id])
        
        change = self.opinions[agent_id] - old_opinion
        
        if source_agent:
            logging.info(f"Opinion change - {agent_id}: {old_opinion:.2f} → {self.opinions[agent_id]:.2f} ({change:+.2f}) [influenced by {source_agent}]")
        else:
            logging.info(f"Opinion change - {agent_id}: {old_opinion:.2f} → {self.opinions[agent_id]:.2f} ({change:+.2f})")
    
    def _record_vote(self, agent_id: str, vote: str):
        """Record an agent's vote."""
        self.votes[agent_id] = vote
        self.vote_count += 1
        logging.info(f"Agent {agent_id} votes: {vote}")
        
        # Check if consensus or majority is reached
        self._check_consensus()
    
    def _check_consensus(self):
        """Check if consensus has been reached and handle dissenting agent."""
        if len(self.votes) == 0:
            return
        
        for_votes = sum(1 for v in self.votes.values() if v == 'for')
        total_votes = len(self.votes)
        agreement_rate = for_votes / total_votes if total_votes > 0 else 0
        
        # Check for consensus (75%+)
        if agreement_rate >= self.consensus_threshold:
            logging.info(f"CONSENSUS REACHED! {for_votes}/{total_votes} agents voted 'for'")
            
            # Check if anyone still disagrees
            against_voters = [agent_id for agent_id, vote in self.votes.items() if vote == 'against']
            abstain_voters = [agent_id for agent_id, vote in self.votes.items() if vote == 'abstain']
            
            if against_voters and not self.dissent_turn_used:
                # Give one turn to the dissenting agent
                self.dissenting_agent = against_voters[0]
                self.final_voting = True
                logging.info(f"Consensus reached but {self.dissenting_agent} still opposes. They have one turn to convince others.")
            else:
                self.is_consensus = True
                logging.info("FINAL: Debate ended with consensus")
        
        elif agreement_rate >= 0.5:
            logging.info(f"MAJORITY REACHED! {for_votes}/{total_votes} agents voted 'for'")
    
    def env_step(self):
        """Advance the environment by one step."""
        super().env_step()
        
        # Check if debate deadline has been reached
        if self.step >= self.debate_deadline and not self.voting_forced and not self.is_consensus:
            self._force_voting_phase()
        
        self._print_step_summary()
        # Reset message counter for next step
        self.messages_this_step = {}
    
    def _force_voting_phase(self):
        """Force all agents to vote after debate deadline."""
        self.voting_forced = True
        logging.info("=" * 60)
        logging.info(f"DEBATE DEADLINE REACHED (Step {self.step})")
        logging.info("All agents must now vote immediately!")
        logging.info("=" * 60)
    
    def _print_step_summary(self):
        """Print opinion summary for this step."""
        logging.info("=" * 60)
        logging.info(f"STEP {self.step} SUMMARY")
        logging.info("=" * 60)
        
        logging.info("Current Opinions:")
        for agent_id in sorted(self.opinions.keys()):
            current = self.opinions[agent_id]
            previous = self.opinion_history[agent_id][-2] if len(self.opinion_history[agent_id]) > 1 else current
            change = current - previous
            change_str = f"{change:+.2f}" if change != 0 else "±0.00"
            logging.info(f"  {agent_id}: {current:7.2f} ({change_str})")
        
        if self.votes:
            logging.info(f"Votes: {self.votes}")
        logging.info("=" * 60)
    
    def get_prompt(self):
        """Get context for agents about the debate state."""
        opinion_summary = "\n".join([
            f"  {agent_id}: {opinion:.2f}" 
            for agent_id, opinion in sorted(self.opinions.items())
        ])
        
        vote_summary = "\n".join([
            f"  {agent_id}: {vote}"
            for agent_id, vote in sorted(self.votes.items())
        ]) or "  No votes yet"
        
        recent_messages = [arg for arg in self.arguments if arg.get('step') == self.step][-3:]
        msg_summary = "\n".join([
            f"  {msg['from']} → {msg['to']}: {msg['message']}"
            for msg in recent_messages
        ]) or "  No recent messages"
        
        relationships_str = ""
        if self.relationships:
            rel_lines = []
            for agent_id in sorted(self.opinions.keys()):
                if agent_id in self.relationships:
                    rel_lines.append(f"  {agent_id}: {', '.join([f'{other}({rel})' for other, rel in self.relationships[agent_id].items()])}")
            relationships_str = "\nAgent Relationships:\n" + "\n".join(rel_lines) if rel_lines else ""
        
        # Add deadline warning
        deadline_warning = ""
        steps_left = self.debate_deadline - self.step
        if steps_left > 0 and not self.voting_forced:
            deadline_warning = f"\n⏰ DEBATE DEADLINE: {steps_left} step(s) left before MANDATORY VOTING!"
        elif self.voting_forced:
            deadline_warning = f"\n🔴 VOTING PHASE ACTIVE: You MUST vote NOW. Use action: {{\"action\": \"interact_env\", \"env_action\": \"vote\", \"params\": {{\"vote\": \"for|against|abstain\"}}}}"
        
        return f"""
╔════════════════════════════════════════════════════════════╗
║ DEBATE STATE
╚════════════════════════════════════════════════════════════╝
Topic: {self.topic}
Status: {"Consensus Reached" if self.is_consensus else ("🔴 VOTING PHASE" if self.voting_forced else "⚔️  DEBATE IN PROGRESS")}{deadline_warning}

Current Opinions (-1.0=against, 0.0=neutral, 1.0=for):
{opinion_summary}

Votes Cast ({len(self.votes)}/{len(self.opinions)}):
{vote_summary}

Recent Messages:
{msg_summary}
{relationships_str}
"""
    
    def get_context(self):
        """Return full debate context for agents."""
        base = super().get_context()
        return f"{base}\n{self.get_prompt()}"
