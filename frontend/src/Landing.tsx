import './Landing.css'

// Pre-computed layout so the dice are spread evenly and don't reposition on re-render
const DICE_LAYOUT: Array<{
  symbol: string
  top: string
  left: string
  duration: string
  delay: string
  size: string
}> = [
  { symbol: '⚅', top: '8%',  left: '6%',  duration: '9.1s',  delay: '0s',    size: '3.6rem' },
  { symbol: '⚀', top: '15%', left: '22%', duration: '11.4s', delay: '1.2s',  size: '2.8rem' },
  { symbol: '⚃', top: '5%',  left: '45%', duration: '8.7s',  delay: '0.4s',  size: '3.1rem' },
  { symbol: '⚂', top: '11%', left: '68%', duration: '12.2s', delay: '2.1s',  size: '2.6rem' },
  { symbol: '⚄', top: '7%',  left: '86%', duration: '9.8s',  delay: '0.8s',  size: '3.4rem' },
  { symbol: '⚁', top: '35%', left: '3%',  duration: '13.1s', delay: '1.7s',  size: '2.4rem' },
  { symbol: '⚅', top: '42%', left: '92%', duration: '10.3s', delay: '0.2s',  size: '3.0rem' },
  { symbol: '⚀', top: '62%', left: '10%', duration: '11.7s', delay: '2.5s',  size: '2.9rem' },
  { symbol: '⚃', top: '58%', left: '80%', duration: '8.4s',  delay: '1.0s',  size: '3.3rem' },
  { symbol: '⚂', top: '78%', left: '30%', duration: '14.0s', delay: '0.6s',  size: '2.5rem' },
  { symbol: '⚄', top: '82%', left: '55%', duration: '9.5s',  delay: '1.9s',  size: '3.8rem' },
  { symbol: '⚁', top: '88%', left: '76%', duration: '12.6s', delay: '0.3s',  size: '2.7rem' },
  { symbol: '⚅', top: '70%', left: '47%', duration: '10.8s', delay: '3.0s',  size: '2.2rem' },
  { symbol: '⚀', top: '50%', left: '60%', duration: '7.9s',  delay: '1.4s',  size: '3.2rem' },
  { symbol: '⚃', top: '28%', left: '38%', duration: '13.5s', delay: '2.8s',  size: '2.3rem' },
]

const TEAM = [
  { name: 'Vishnu Nair',  img: '/vishnu.jpg' },
  { name: 'Julian Park',  img: '/julian.jpg' },
  { name: 'David Chen',   img: '/david.jpg' },
  { name: 'Rishi Shah',   img: '/0908f915-ccc0-46f7-a61e-453a2988a750.JPG' },
]

interface LandingProps {
  onEnter: () => void
  leaving: boolean
}

export default function Landing({ onEnter, leaving }: LandingProps) {
  return (
    <div className={`landing${leaving ? ' leaving' : ''}`}>
      {/* Floating dice */}
      <div className="landing-dice" aria-hidden="true">
        {DICE_LAYOUT.map((d, i) => (
          <span
            key={i}
            className="landing-die"
            style={{
              top: d.top,
              left: d.left,
              fontSize: d.size,
              animationDuration: d.duration,
              animationDelay: d.delay,
            }}
          >
            {d.symbol}
          </span>
        ))}
      </div>

      {/* Main content */}
      <div className="landing-content">
        <p className="landing-eyebrow">Board Game Recommender</p>

        <h1 className="landing-title">
          Find your next<br />
          <em>favourite game</em>
        </h1>

        <div className="landing-divider" />

        <p className="landing-subtitle">
          Discover board games using latent SVD themes and AI-powered query
          rewriting. Tell us what you love — we'll find what's next.
        </p>

        <button className="landing-cta" onClick={onEnter}>
          Start Exploring
        </button>

        {/* Team section */}
        <div className="landing-team">
          <p className="landing-team-label">Meet the Team</p>
          <div className="landing-team-members">
            {TEAM.map((member) => (
              <div key={member.name} className="landing-member">
                <div className="landing-member-avatar">
                  {member.img
                    ? <img src={member.img} alt={member.name} />
                    : <span>{member.name.split(' ').map((w) => w[0]).join('')}</span>
                  }
                </div>
                <p className="landing-member-name">{member.name}</p>
                <p className="landing-member-meta">Cornell CS '27</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <p className="landing-hint">Powered by TF-IDF · SVD · LLM</p>
    </div>
  )
}
